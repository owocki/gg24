import csv
import urllib.request
import urllib.error
import os
import time
from urllib.parse import urlparse

def download_posts():
    with open('data.csv', 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        for index, row in enumerate(csv_reader, start=1):
            link = row['Link']
            title = row['Title']
            submitted_by = row['Submitted By']
            date = row['Date Submitted']
            
            print(f"Downloading post {index}: {title}")
            
            try:
                with urllib.request.urlopen(link, timeout=30) as response:
                    html_content = response.read().decode('utf-8')
                
                url_parts = urlparse(link)
                path_parts = url_parts.path.strip('/').split('/')
                
                if len(path_parts) >= 2:
                    post_id = path_parts[-1]
                else:
                    post_id = f"post_{index}"
                
                # Use post ID from URL for filename
                filename = f"posts/{post_id}.html"
                
                with open(filename, 'w', encoding='utf-8') as post_file:
                    post_file.write(html_content)
                
                print(f"  ✓ Saved to {filename}")
                
                time.sleep(1)
                
            except urllib.error.URLError as e:
                print(f"  ✗ Error downloading {link}: {e}")
            except Exception as e:
                print(f"  ✗ Unexpected error: {e}")

if __name__ == "__main__":
    download_posts()
    print("\nAll posts downloaded successfully!")