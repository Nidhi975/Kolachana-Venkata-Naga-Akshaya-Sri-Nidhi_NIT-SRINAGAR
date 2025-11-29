"""
Create Sample Test Bill
Generates a simple test bill image for testing the extraction system
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os


def create_sample_bill(output_path="test_bill.jpg"):
    """
    Create a simple sample medical bill for testing
    
    Args:
        output_path: Where to save the generated bill
    """
    # Create white background
    width, height = 800, 1000
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # Convert to PIL for better text rendering
    pil_img = Image.fromarray(img)
    draw = ImageDraw.Draw(pil_img)
    
    # Try to use a better font, fallback to default
    try:
        title_font = ImageFont.truetype("arial.ttf", 32)
        header_font = ImageFont.truetype("arial.ttf", 20)
        normal_font = ImageFont.truetype("arial.ttf", 16)
    except:
        # Fallback to default font
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
    
    y_pos = 50
    
    # Hospital Header
    draw.text((width//2 - 150, y_pos), "CITY GENERAL HOSPITAL", fill=(0, 0, 0), font=title_font)
    y_pos += 50
    
    draw.text((width//2 - 120, y_pos), "Medical Bill / Invoice", fill=(0, 0, 0), font=header_font)
    y_pos += 60
    
    # Bill Details
    draw.text((50, y_pos), "Bill No: MED-2025-001", fill=(0, 0, 0), font=normal_font)
    y_pos += 30
    draw.text((50, y_pos), "Date: 29-Nov-2025", fill=(0, 0, 0), font=normal_font)
    y_pos += 30
    draw.text((50, y_pos), "Patient: John Doe", fill=(0, 0, 0), font=normal_font)
    y_pos += 60
    
    # Table Header
    draw.text((50, y_pos), "Description", fill=(0, 0, 0), font=header_font)
    draw.text((500, y_pos), "Amount (INR)", fill=(0, 0, 0), font=header_font)
    y_pos += 5
    
    # Draw line
    draw.line([(50, y_pos), (750, y_pos)], fill=(0, 0, 0), width=2)
    y_pos += 30
    
    # Line Items
    items = [
        ("Doctor Consultation Fee", 500.00),
        ("Blood Test - Complete", 800.00),
        ("X-Ray Chest", 600.00),
        ("Paracetamol Tablets (10)", 50.00),
        ("Antibiotic Capsules (5)", 250.00),
        ("Room Charges (1 day)", 1500.00),
        ("Nursing Charges", 400.00),
    ]
    
    for description, amount in items:
        draw.text((50, y_pos), description, fill=(0, 0, 0), font=normal_font)
        draw.text((550, y_pos), f"₹ {amount:.2f}", fill=(0, 0, 0), font=normal_font)
        y_pos += 35
    
    y_pos += 20
    
    # Draw line before total
    draw.line([(50, y_pos), (750, y_pos)], fill=(0, 0, 0), width=1)
    y_pos += 30
    
    # Total
    total = sum(amount for _, amount in items)
    draw.text((50, y_pos), "TOTAL AMOUNT", fill=(0, 0, 0), font=header_font)
    draw.text((550, y_pos), f"₹ {total:.2f}", fill=(0, 0, 0), font=header_font)
    y_pos += 60
    
    # Footer
    draw.text((50, y_pos), "Thank you for choosing City General Hospital", fill=(100, 100, 100), font=normal_font)
    y_pos += 30
    draw.text((50, y_pos), "For queries, contact: billing@cityhospital.com", fill=(100, 100, 100), font=normal_font)
    
    # Convert back to OpenCV format and save
    img_array = np.array(pil_img)
    cv2.imwrite(output_path, img_array)
    
    print(f"✅ Sample bill created: {output_path}")
    print(f"   Size: {os.path.getsize(output_path) / 1024:.2f} KB")
    print(f"   Dimensions: {width}x{height}")
    print(f"\n📊 Bill Details:")
    print(f"   Total Items: {len(items)}")
    print(f"   Total Amount: ₹ {total:.2f}")
    print(f"\n💡 Test it with:")
    print(f"   python submit_bill.py {output_path}")


if __name__ == "__main__":
    import sys
    
    output_file = sys.argv[1] if len(sys.argv) > 1 else "test_bill.jpg"
    create_sample_bill(output_file)
