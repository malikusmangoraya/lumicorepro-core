import os
import urllib.request

base_dir = r"c:\Users\AZAM COMPUTERS\OneDrive\Desktop\lumicorepro-core"
img_dir = os.path.join(base_dir, "src", "assets", "images")
icon_dir = os.path.join(base_dir, "src", "icons")

os.makedirs(img_dir, exist_ok=True)
os.makedirs(icon_dir, exist_ok=True)

categories = [
    "business", "ecommerce", "realestate", "restaurant", "portfolio",
    "education", "healthcare", "fitness", "travel", "creative"
]

for cat in categories:
    os.makedirs(os.path.join(img_dir, cat), exist_ok=True)

# Unsplash Top Quality Photo URLs
photo_urls = [
    ("business", "corporate-hero.jpg", "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=1000&auto=format&fit=crop"),
    ("business", "office-team.jpg", "https://images.unsplash.com/photo-1522071820081-009f0129c71c?q=80&w=1000&auto=format&fit=crop"),
    ("business", "executive.jpg", "https://images.unsplash.com/photo-1560250097-0b93528c311a?q=80&w=1000&auto=format&fit=crop"),
    ("ecommerce", "iphone-pro.jpg", "https://images.unsplash.com/photo-1695048133142-1a20484d2569?q=80&w=1000&auto=format&fit=crop"),
    ("ecommerce", "macbook-pro.jpg", "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=1000&auto=format&fit=crop"),
    ("ecommerce", "sony-headphones.jpg", "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=1000&auto=format&fit=crop"),
    ("realestate", "modern-house.jpg", "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?q=80&w=1000&auto=format&fit=crop"),
    ("realestate", "luxury-villa.jpg", "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=1000&auto=format&fit=crop"),
    ("restaurant", "fine-dining.jpg", "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=1000&auto=format&fit=crop"),
    ("restaurant", "gourmet-dish.jpg", "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=1000&auto=format&fit=crop"),
    ("portfolio", "developer-workspace.jpg", "https://images.unsplash.com/photo-1498050108023-c5249f4df085?q=80&w=1000&auto=format&fit=crop"),
    ("portfolio", "designer-portrait.jpg", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=1000&auto=format&fit=crop"),
    ("education", "student-library.jpg", "https://images.unsplash.com/photo-1523240795612-9a054b0db644?q=80&w=1000&auto=format&fit=crop"),
    ("education", "online-course.jpg", "https://images.unsplash.com/photo-1501504905252-473c47e087f8?q=80&w=1000&auto=format&fit=crop"),
    ("healthcare", "modern-hospital.jpg", "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?q=80&w=1000&auto=format&fit=crop"),
    ("healthcare", "doctor-consult.jpg", "https://images.unsplash.com/photo-1622253692010-333f2da6031d?q=80&w=1000&auto=format&fit=crop"),
    ("fitness", "gym-workout.jpg", "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=1000&auto=format&fit=crop"),
    ("fitness", "personal-trainer.jpg", "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?q=80&w=1000&auto=format&fit=crop"),
    ("travel", "beach-resort.jpg", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1000&auto=format&fit=crop"),
    ("travel", "mountain-tour.jpg", "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=1000&auto=format&fit=crop"),
    ("creative", "studio-agency.jpg", "https://images.unsplash.com/photo-1542744094-3a3172720177?q=80&w=1000&auto=format&fit=crop"),
    ("creative", "artwork-design.jpg", "https://images.unsplash.com/photo-1513364776144-60967b0f800f?q=80&w=1000&auto=format&fit=crop")
]

req_headers = {"User-Agent": "Mozilla/5.0"}
downloaded = 0

for cat, fname, url in photo_urls:
    target_path = os.path.join(img_dir, cat, fname)
    try:
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req) as resp, open(target_path, "wb") as f:
            f.write(resp.read())
        print(f"Downloaded: {cat}/{fname}")
        downloaded += 1
    except Exception as e:
        print(f"Failed to download {cat}/{fname}: {e}")

print(f"Total downloaded assets: {downloaded}")
