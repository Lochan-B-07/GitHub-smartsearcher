import os
import re
import sys
import argparse
import time
from datetime import datetime, timezone
import chromadb
from chromadb.utils import embedding_functions
from github import Github, Auth, RateLimitExceededException, GithubException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_github_client():
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN not found in environment. Proceeding anonymously (limited rate limits).")
        return Github()
    else:
        auth = Auth.Token(GITHUB_TOKEN)
        return Github(auth=auth)

g = get_github_client()

def clean_markdown(text):
    if not text:
        return ""
    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Remove inline code
    text = re.sub(r'`[^`]+`', '', text)
    # Remove badges and images
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Convert markdown links [text](url) to just "text"
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    # Remove headings syntax (#)
    text = re.sub(r'#+\s+', '', text)
    # Remove formatting characters like **, *, __, _
    text = re.sub(r'\*\*|__|\*|_', '', text)
    # Remove table grid lines
    text = re.sub(r'\|', ' ', text)
    # Remove leading dash/bullet indicators from lines
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def chunk_text(text, max_words=500):
    words = text.split()
    return [' '.join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

def setup_database():
    print("Connecting to local ChromaDB...")
    client = chromadb.PersistentClient(path="./chroma_data")
    default_ef = embedding_functions.DefaultEmbeddingFunction()
    
    collection = client.get_or_create_collection(
        name="github_repos", 
        embedding_function=default_ef
    )
    return collection

def ingest_data(collection, language="Python", max_repos=50):
    print(f"Fetching top {max_repos} starred {language} repositories...")
    
    query = f"stars:>1000 language:{language}"
    
    try:
        # Sort by stars descending
        repositories = g.search_repositories(query=query, sort="stars", order="desc")
        
        count = 0
        for repo in repositories:
            if count >= max_repos:
                break
            
            print(f"Processing ({count+1}/{max_repos}): {repo.full_name}")
            
            try:
                readme_file = repo.get_readme()
                readme_content = readme_file.decoded_content.decode("utf-8")
            except GithubException as ge:
                if ge.status == 404:
                    print(f"  -> No README found (Skip)")
                else:
                    print(f"  -> Error fetching README: {ge.message}")
                continue
            except Exception as e:
                print(f"  -> Could not fetch README (Skip): {e}")
                continue
                
            cleaned_text = clean_markdown(readme_content)
            chunks = chunk_text(cleaned_text, max_words=500)
            
            # We also want the repo's description
            desc = repo.description or ""
            
            # Clear old chunks of this repository to prevent duplicates
            try:
                collection.delete(where={"name": repo.full_name})
            except Exception:
                pass
            
            for idx, chunk in enumerate(chunks):
                # To avoid saving meaningless small chunks
                if len(chunk.split()) < 20: 
                    continue
                    
                chunk_id = f"{repo.id}_chunk_{idx}"
                
                # Use description + chunk content as the document
                document_text = f"{desc}. {chunk}"
                
                metadata = {
                    "name": repo.full_name,
                    "url": repo.html_url,
                    "language": language,
                    "stars": repo.stargazers_count
                }
                
                # Upsert into ChromaDB
                collection.upsert(
                    ids=[chunk_id],
                    documents=[document_text],
                    metadatas=[metadata]
                )
                
            count += 1
            
    except RateLimitExceededException:
        print("\n[ERROR] GitHub API rate limit exceeded.")
        if not GITHUB_TOKEN:
            print("Please configure a GITHUB_TOKEN in your .env file to get higher limits (5,000 requests/hr).")
        else:
            try:
                rate_limit = g.get_rate_limit()
                reset_time = rate_limit.core.reset
                sleep_seconds = int((reset_time - datetime.now(timezone.utc)).total_seconds()) + 5
                print(f"Rate limit resets in {sleep_seconds} seconds.")
            except Exception:
                pass
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred during search: {e}")
        sys.exit(1)
        
    print(f"Data ingestion for {language} complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest trending GitHub repositories into local vector database.")
    parser.add_argument("-l", "--language", type=str, default="Python",
                        help="The programming language to search for (default: Python). Use 'all' to fetch default set.")
    parser.add_argument("-m", "--max-repos", type=int, default=50,
                        help="Maximum number of repositories to ingest (default: 50).")
    args = parser.parse_args()
    
    db_collection = setup_database()
    
    if args.language.lower() == "all":
        # Ingest top repos across multiple languages
        default_languages = ["Python", "JavaScript", "TypeScript", "Rust", "Go"]
        # Reduce max repos per language when running "all" to be friendly to rate limits
        repos_per_lang = max(10, args.max_repos // len(default_languages))
        print(f"Ingesting top {repos_per_lang} repositories for: {', '.join(default_languages)}")
        for lang in default_languages:
            try:
                ingest_data(db_collection, language=lang, max_repos=repos_per_lang)
            except Exception as e:
                print(f"Failed to ingest for {lang}: {e}")
    else:
        # Standard capitalization
        lang_cap = args.language.capitalize()
        # Handle special language casings
        if args.language.lower() == "javascript":
            lang_cap = "JavaScript"
        elif args.language.lower() == "typescript":
            lang_cap = "TypeScript"
        
        ingest_data(db_collection, language=lang_cap, max_repos=args.max_repos)

