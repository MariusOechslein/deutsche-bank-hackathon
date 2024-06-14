import chromadb

def retrieve_context(collection,query,max_results,distance_threshold = 0.5,print_t = False):

    results = collection.query(query_texts=query, n_results=max_results, include=['metadatas','documents','distances'])

    distances = results['distances'][0]
    documents = results['documents'][0]
    ids = results['ids'][0]
    metadatas = results['metadatas'][0]

    # Define keys for the dictionaries
    keys = ['id', 'distance', 'text', 'metadata']

    # Combine lists using zip and create a list of dictionaries
    results = [dict(zip(keys, values)) for values in zip(ids, distances, documents, metadatas)]

    # Apply the filter using a list comprehension
    filtered_data = [item for item in results if item['distance'] < distance_threshold]

    if(print_t):
        for j in filtered_data:
            print(j)
    
    return filtered_data