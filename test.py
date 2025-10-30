"""
Complete rebuild with proper verification.
"""

import os
import shutil
from pathlib import Path

print("=" * 60)
print("COMPLETE VECTOR STORE REBUILD")
print("=" * 60)

# Step 1: Delete old data
print("\n1. Deleting old vector store...")
chroma_path = Path("./data/chroma_db")
if chroma_path.exists():
    shutil.rmtree(chroma_path)
    print("   ✓ Deleted")

# Step 2: Verify embeddings
print("\n2. Verifying embeddings configuration...")
from retrieval.vector_store import initialize_embeddings

embeddings = initialize_embeddings()
embed_type = type(embeddings).__name__
test_dim = len(embeddings.embed_query("test"))

print(f"   ✓ Type: {embed_type}")
print(f"   ✓ Dimension: {test_dim}")

# Step 3: Run ingestion
print("\n3. Running ingestion (this takes ~30 seconds)...")
result = os.system("python ingest_data.py --reset")

if result != 0:
    print("   ✗ Ingestion failed!")
    exit(1)

# Step 4: Verify data using same interface as ingestion
print("\n4. Verifying data was saved...")
from retrieval.vector_store import initialize_vector_store

try:
    vectorstore = initialize_vector_store()
    
    # Get collection using Langchain interface
    collection = vectorstore._collection
    count = collection.count()
    
    print(f"   ✓ Documents in database: {count}")
    
    if count == 0:
        print("   ✗ Database is empty!")
        exit(1)
        
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 5: Test retrieval
print("\n5. Testing retrieval...")
from retrieval.vector_store import search_vectorstore

results = search_vectorstore(vectorstore, "4 bedroom villa with pool", k=3)

print(f"   ✓ Retrieved: {len(results)} documents")

if len(results) == 0:
    print("\n   ✗ STILL NOT WORKING!")
    print("\n   Checking what's in the database...")
    
    # Try to get all documents
    all_docs = collection.get(limit=5)
    print(f"   - Total documents in collection: {len(all_docs['ids'])}")
    
    if all_docs['documents']:
        print(f"   - Sample document: {all_docs['documents'][0][:100]}...")
        print(f"   - Sample metadata: {all_docs['metadatas'][0]}")
    
    # Check embeddings
    if all_docs['embeddings']:
        stored_dim = len(all_docs['embeddings'][0])
        print(f"   - Stored embedding dimension: {stored_dim}")
        print(f"   - Current embedding dimension: {test_dim}")
        
        if stored_dim != test_dim:
            print(f"\n   ✗ DIMENSION MISMATCH!")
    
    exit(1)

# Success!
print("\n" + "=" * 60)
print("✅ SUCCESS! VECTOR STORE IS WORKING!")
print("=" * 60)
print("\nSample results:")
for i, result in enumerate(results[:2], 1):
    print(f"\n{i}. Content: {result.page_content[:100]}...")
    print(f"   Page: {result.metadata.get('page')}")
    print(f"   Type: {result.metadata.get('source_type')}")

print("\n✅ You can now run: python app.py")
print("=" * 60)