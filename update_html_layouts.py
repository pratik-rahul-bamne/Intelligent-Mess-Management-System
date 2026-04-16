import os
import re

# Read the template from dashboard.html
with open('dashboard.html', 'r', encoding='utf-8') as f:
    dashboard_content = f.read()

# Extract the sidebar + header block
sidebar_regex = re.compile(r'(\s*<!-- Sidebar -->\s*<aside class="sidebar".*?</header>\s*)', re.DOTALL)
match = sidebar_regex.search(dashboard_content)
if not match:
    print("Could not find sidebar/header in dashboard.html")
    exit(1)

template_block = match.group(1)
# Remove the active class from dashboard link
template_block = template_block.replace('<a href="dashboard.html" class="active">', '<a href="dashboard.html">')

# Files to update and their new headers
files_to_update = {
    'meals.html': ("Meals Management", "Manage menus and dietary preferences"),
    'attendance.html': ("Attendance", "Track user dining check-ins realtime"),
    'billing.html': ("Billing & Invoices", "Manage student payments and invoices"),
    'inventory.html': ("Inventory Control", "Monitor stock levels and suppliers"),
    'reports.html': ("Analytics & Reports", "View insights and export data"),
    'users.html': ("User Management", "Manage students, staff, and admins"),
    'feedback.html': ("Feedback", "Review user ratings and complaints"),
    'settings.html': ("System Settings", "Configure application parameters"),
    'profile.html': ("User Profile", "Manage your account details")
}

for filename, (title, subtitle) in files_to_update.items():
    if not os.path.exists(filename):
        continue
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace sidebar+header
    content = sidebar_regex.sub(template_block, content)
    
    # Replace the old page title e.g. <h2 class="page-title">...</h2>
    # with the new structured title block
    title_regex = re.compile(r'(\s*)<h2 class="page-title">.*?</h2>')
    
    new_title_block = f'''\\1<div class="mb-6">
\\1    <h2 class="page-title">{title}</h2>
\\1    <p class="page-subtitle">{subtitle}</p>
\\1</div>'''
    
    content = title_regex.sub(new_title_block, content, count=1)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Updated {filename}")

print("Done updating layouts.")
