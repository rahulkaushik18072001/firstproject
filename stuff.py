import json

def create_html_from_json(json_file, output_file):
    # Read the JSON file as a single array of objects
    with open(json_file, 'r', encoding='utf-8') as f:
        articles = json.load(f)  # Use json.load for standard JSON arrays

    # Generate HTML content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>News Articles</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }
            .article {
                margin-bottom: 40px;
                padding: 20px;
                border: 1px solid #ccc;
                border-radius: 10px;
            }
            .article-title {
                font-size: 24px;
                font-weight: bold;
                color: #333;
            }
            .article-description {
                font-size: 16px;
                margin-top: 10px;
                color: #666;
            }
            .article-text {
                margin-top: 20px;
            }
            .article-meta {
                font-size: 14px;
                color: #999;
                margin-top: 10px;
            }
            a {
                color: #007BFF;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
    """

    for article in articles:
        html_content += f"""
        <div class="article">
            <div class="article-title">{article.get('title', 'No Title')}</div>
            <div class="article-description">{article.get('description', 'No Description')}</div>
            <div class="article-meta">
                <strong>Authors:</strong> {', '.join(article.get('authors', [])) or 'Unknown'}<br>
                <strong>Published Date:</strong> {article.get('date_publish', 'Unknown')}<br>
                <strong>URL:</strong> <a href="{article.get('url', '#')}" target="_blank">{article.get('url', 'No URL')}</a>
            </div>
            <div class="article-text">{article.get('text', 'No Content')}</div>
        </div>
        """

    html_content += """
    </body>
    </html>
    """

    # Save the HTML content to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

# Specify your JSON file and output HTML file
json_file = 'articles.json'  # Replace with your JSON file
output_file = 'articles.html'  # Replace with your desired HTML output file

# Generate the HTML file
create_html_from_json(json_file, output_file)

print(f"HTML file '{output_file}' has been created successfully.")
