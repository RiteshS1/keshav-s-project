from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from django.shortcuts import render
import pandas as pd
import joblib

# Load the data and models
data = pd.read_pickle('myApp/dataset/data.pkl')
preprocessor = joblib.load('myApp/models/preprocessor.joblib')
kmeans = joblib.load('myApp/models/kmeans_model.joblib')

# Transform the features and reduce dimensionality
feature_matrix = preprocessor.fit_transform(data)

# Apply TruncatedSVD for dimensionality reduction
svd = TruncatedSVD(n_components=50)  # Adjust n_components as needed
feature_matrix = svd.fit_transform(feature_matrix)

# Compute the cosine similarity matrix
cosine_sim = cosine_similarity(feature_matrix, feature_matrix)

def home(request):
    return render(request, 'index.html')

def get_recommendations(search_param, n_recommendations=6):
    # Filter data based on search parameter
    search_results = data[data['Title'].str.contains(search_param, case=False) |
                          (data['Category'] == search_param) |
                          (data['Sub-Category'] == search_param)]

    # If no results found, return an empty DataFrame
    if search_results.empty:
        return pd.DataFrame()

    cluster_label = kmeans.labels_[search_results.index[0]]

    # Get the indices of products in the same cluster
    cluster_indices = [i for i, label in enumerate(kmeans.labels_) if label == cluster_label]

    # Get the pairwise similarity scores within the cluster
    sim_scores = [(i, cosine_sim[search_results.index[0]][i]) for i in cluster_indices]

    # Sort the products based on similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the top N most similar products
    sim_scores = sim_scores[:n_recommendations]
    product_indices = [i[0] for i in sim_scores]
    
    recommendations_kmeans = []

    # Append the recommendations to the list
    for idx in product_indices:
        recommendations_kmeans.append({
            'Title': data.iloc[idx]['Title'],
            'Category': data.iloc[idx]['Category'],
            'Sub_Category': data.iloc[idx]['Sub-Category'],
            'Price': data.iloc[idx]['Price'],
            'Ratings': data.iloc[idx]['Ratings'],
            'Total_Ratings': round(data.iloc[idx]['Total Ratings'], 2)
        })

    return recommendations_kmeans

def recommend_products(request):
    if request.method == 'POST':
        title = request.POST.get('product')
        print(title)

        # Get recommendations for the input product title
        recommendations_kmeans = get_recommendations(title)

        return render(request, 'index.html', {'recommendations': recommendations_kmeans})

    return render(request, 'index.html')
