from scipy.spatial.distance import cosine


def calculate_cosine_distances(embeddings):
    distances = []
    # Iterate through consecutive pairs of embeddings to calculate distances
    for i in range(len(embeddings) - 1):
        # Calculate the cosine distance between consecutive embeddings
        distance = cosine(embeddings[i], embeddings[i + 1])
        distances.append(distance)

    return distances
