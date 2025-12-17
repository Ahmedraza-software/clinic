# Inventory Management Setup Guide

## 🏥 Clean Slate Inventory System

Your inventory system has been reset and is ready for you to add your own medical items.

## 📋 What's Already Set Up

### ✅ Categories Available:
- **Medications** - Pharmaceutical drugs and medicines
- **Medical Supplies** - General medical supplies and consumables  
- **Equipment** - Medical equipment and devices
- **Laboratory** - Laboratory supplies and testing materials
- **Emergency** - Emergency medical supplies
- **Office Supplies** - Administrative and office supplies

### ✅ Sample Suppliers Available:
- **Local Medical Supply Co.** - General medical supplies
- **Pharmaceutical Distributor** - Medications and drugs
- **Medical Equipment Supplier** - Medical devices and equipment

## 🚀 Getting Started

### Step 1: Access Inventory
- Navigate to **Inventory** in the sidebar
- You'll see an empty inventory dashboard

### Step 2: Add Your First Item
- Click **"Add Item"** button
- Fill in the item details:
  - **Item Name**: e.g., "Paracetamol 500mg Tablets"
  - **Category**: Select from available categories
  - **Supplier**: Choose or add new supplier
  - **Unit**: e.g., "tablets", "pieces", "boxes"
  - **Price per Unit**: Cost of individual item
  - **Initial Quantity**: Starting stock amount
  - **Minimum Quantity**: Alert threshold for low stock

### Step 3: Manage Your Inventory
- **View Dashboard**: See all items, stock levels, total values
- **Update Stock**: Use the stock update buttons to add/remove inventory
- **Track History**: View all stock movements and changes
- **Export Data**: Download inventory reports

## 💡 Pro Tips

1. **Set Realistic Minimum Quantities**: This helps you get alerts before running out
2. **Use Consistent Units**: Stick to standard units (tablets, pieces, ml, etc.)
3. **Regular Updates**: Update stock levels as you use items
4. **Categorize Properly**: Use the right categories for easy filtering
5. **Track Expiry Dates**: Add expiry dates for medications and perishables

## 🛠️ Management Commands (For Developers)

If you need to reset the inventory again:
```bash
# Clear all inventory data
python manage.py clear_inventory --confirm

# Set up basic categories again
python manage.py setup_basic_categories

# Set up basic suppliers again  
python manage.py setup_basic_suppliers
```

## 📊 Dashboard Features

Your inventory dashboard shows:
- **Total Items**: Count of all inventory items
- **Low Stock Alerts**: Items below minimum quantity
- **Out of Stock**: Items with zero quantity
- **Total Value**: Complete inventory value
- **Stock Status Charts**: Visual representation of inventory health

Start adding your medical inventory items and the system will automatically calculate totals, track stock levels, and alert you when items need restocking!
