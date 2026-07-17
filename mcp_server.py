import os
import chromadb
from chromadb.utils import embedding_functions
from mcp.server.fastmcp import FastMCP
import data_ingestion

# Initialize FastMCP Server
mcp = FastMCP("GitHub Idea Matcher")

# Initialize ChromaDB
def get_db():
    client = chromadb.PersistentClient(path="./chroma_data")
    default_ef = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name="github_repos", 
        embedding_function=default_ef
    )
    return collection

@mcp.tool()
def search_repos(query: str, language: str = "All", n_results: int = 5) -> str:
    """
    Semantically search for GitHub repositories based on a natural language idea or intent.
    
    Parameters:
    - query (str): The project idea, intent, or description to match (e.g., 'fast microservices framework with gRPC').
    - language (str): Optional programming language filter (e.g., 'Python', 'Rust', 'JavaScript', 'TypeScript', 'Go', 'All').
    - n_results (int): Number of top matching results to return (default is 5).
    """
    collection = get_db()
    
    # Check if database is empty
    count = collection.count()
    if count == 0:
        return (
            "The GitHub Idea Matcher database is currently empty. "
            "Please run the 'ingest_repos' tool first (e.g. for language='Python') to populate the database."
        )
        
    where_clause = {}
    if language and language.lower() != "all":
        # standard capitalizations
        lang_cap = language.capitalize()
        if language.lower() == "javascript":
            lang_cap = "JavaScript"
        elif language.lower() == "typescript":
            lang_cap = "TypeScript"
        where_clause = {"language": lang_cap}
        
    query_args = {
        "query_texts": [query],
        "n_results": n_results
    }
    if where_clause:
        query_args["where"] = where_clause
        
    try:
        results = collection.query(**query_args)
    except Exception as e:
        return f"Error querying database: {str(e)}"
        
    if not results or not results['ids'] or len(results['ids'][0]) == 0:
        return f"No matches found for query '{query}' (Filter: {language})."
        
    output = []
    output.append(f"### 🧠 Semantic matches for: '{query}' (Filter: {language})\n")
    
    for i in range(len(results['ids'][0])):
        metadata = results['metadatas'][0][i]
        repo_name = metadata.get('name', 'Unknown')
        repo_url = metadata.get('url', '#')
        repo_lang = metadata.get('language', 'Unknown')
        repo_stars = metadata.get('stars', 0)
        matched_text = results['documents'][0][i]
        
        # Star formatting
        if repo_stars >= 1000:
            stars_str = f"{repo_stars / 1000:.1f}k"
        else:
            stars_str = str(repo_stars)
            
        output.append(f"{i+1}. **[{repo_name}]({repo_url})**")
        output.append(f"   *Language:* `{repo_lang}` | *Stars:* ⭐ {stars_str}")
        output.append(f"   *Matched Context:* {matched_text}")
        output.append("")
        
    return "\n".join(output)

@mcp.tool()
def ingest_repos(language: str = "Python", max_repos: int = 20) -> str:
    """
    Ingest top starred repositories of a specific programming language into the semantic database.
    This runs data ingestion from the GitHub API, retrieves READMEs, chunks/cleans them, and stores embeddings.
    
    Parameters:
    - language (str): Programming language (e.g. 'Python', 'Rust', 'JavaScript', 'TypeScript', 'Go').
    - max_repos (int): Number of top starred repositories to download and process (default: 20).
    """
    # Capitalize correctly
    lang_cap = language.capitalize()
    if language.lower() == "javascript":
        lang_cap = "JavaScript"
    elif language.lower() == "typescript":
        lang_cap = "TypeScript"
        
    # We must ensure GITHUB_TOKEN is set or prompt
    token_present = "yes" if os.getenv("GITHUB_TOKEN") else "no"
    
    try:
        collection = get_db()
        # Trigger ingestion function from data_ingestion module
        data_ingestion.ingest_data(collection, language=lang_cap, max_repos=max_repos)
        
        # Count new database stats
        count = collection.count()
        return (
            f"Successfully completed ingestion for {lang_cap} (max {max_repos} repos). "
            f"Database now contains {count} chunks in total. "
            f"(GitHub Token present: {token_present})"
        )
    except Exception as e:
        return f"Ingestion failed: {str(e)}"

@mcp.resource("github-ideas://stats")
def get_db_stats() -> str:
    """
    Get statistics about the local vector database.
    """
    try:
        collection = get_db()
        count = collection.count()
        
        # Get unique languages if possible
        results = collection.get(include=["metadatas"])
        languages = set()
        repos = set()
        if results and results.get("metadatas"):
            for meta in results["metadatas"]:
                if meta.get("language"):
                    languages.add(meta["language"])
                if meta.get("name"):
                    repos.add(meta["name"])
                    
        return (
            f"### 📊 GitHub Idea Matcher Database Stats\n\n"
            f"- **Total Semantic Chunks:** {count}\n"
            f"- **Indexed Repositories:** {len(repos)}\n"
            f"- **Languages Available:** {', '.join(languages) if languages else 'None'}"
        )
    except Exception as e:
        return f"Error retrieving stats: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
