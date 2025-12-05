# Authorized Users Python Scripts

Python scripts to programmatically create authorized users in your BandBox system.

## 📁 Available Scripts

### 1. `create_authorized_user.py`
Create individual authorized users interactively.

### 2. `bulk_create_authorized_users.py`
Create multiple authorized users at once from CSV or manual entry.

## 🚀 Usage

### Single User Creation

**Interactive Mode:**
```bash
python create_authorized_user.py
```

The script will:
1. Show available organizations
2. Ask for user email
3. Ask you to select organization
4. Ask you to select role
5. Ask for optional details (name, note)
6. Create the authorized user

**Example Output:**
```
=== Create Authorized User ===

Available Organizations:
1. Red Sox Baseball Club (ID: a1b2c3d4-...)
2. Yankees Baseball Team (ID: e5f6g7h8-...)

==================================================

Enter user email: newplayer@redsox.com

Select organization:
Enter number (1-2): 1

Select role:
1. player
2. coach
3. admin
4. admin-team
5. admin-org
Enter number (1-5): 1

Enter full name (optional, press Enter to skip): Mike Trout
Enter authorization note (optional, press Enter to skip): Center fielder

Creating authorized user...

✅ Authorized user created successfully!
   Email: newplayer@redsox.com
   Organization: Red Sox Baseball Club
   Assigned Role: player
   Name: Mike Trout
   Note: Center fielder
   Record ID: xyz123...

📧 newplayer@redsox.com can now sign up and will be automatically assigned to this organization.
```

### Bulk User Creation

**From CSV File:**

1. **Create sample CSV:**
   ```bash
   python bulk_create_authorized_users.py --sample
   ```
   
   This creates `sample_users.csv`:
   ```csv
   email,full_name,assigned_role,authorization_note
   player1@team.com,John Doe,player,Starting pitcher
   player2@team.com,Jane Smith,player,Center fielder
   coach@team.com,Bob Johnson,coach,Head Coach
   ```

2. **Edit the CSV file** with your users

3. **Import users:**
   ```bash
   python bulk_create_authorized_users.py
   ```
   
   Then select option 1 and provide your CSV file path.

**Manual Entry:**
```bash
python bulk_create_authorized_users.py
```

Then select option 2 and enter users one by one.

**Example Output:**
```
=== Bulk Create Authorized Users ===

Available Organizations:
1. Red Sox Baseball Club (ID: a1b2c3d4-...)

==================================================

Select organization (1-1): 1

Options:
1. Load from CSV file
2. Enter users manually

Select option (1 or 2): 1
Enter CSV file path: my_team_roster.csv

✅ Loaded 15 users from my_team_roster.csv

Authorizing user ID (optional): 

📋 Ready to create 15 users for 'Red Sox Baseball Club'
Continue? (y/n): y

==================================================
CREATING USERS
==================================================

[1/15] Processing: player1@redsox.com
  ✅ Created: player
[2/15] Processing: player2@redsox.com
  ✅ Created: player
[3/15] Processing: coach@redsox.com
  ✅ Created: coach
...

==================================================
SUMMARY
==================================================
✅ Successfully created: 15
⏭️  Skipped (already exist): 0
❌ Failed: 0
📊 Total processed: 15
```

## 📋 CSV File Format

**Required columns:**
- `email` - Email address (required)
- `full_name` - Full name (optional, can be empty)
- `assigned_role` - Role to assign (required)
- `authorization_note` - Note about authorization (optional)

**Valid roles:**
- `player` - Basic access
- `coach` - Can edit and upload data
- `admin` - Can manage team
- `admin-team` - Can manage team users
- `admin-org` - Full organization control

**Example CSV:**
```csv
email,full_name,assigned_role,authorization_note
john.doe@team.com,John Doe,player,Starting pitcher - right handed
jane.smith@team.com,Jane Smith,player,Outfielder - excellent defense
bob.coach@team.com,Bob Johnson,coach,Head Coach - 20 years experience
mary.admin@team.com,Mary Williams,admin-team,Team Administrator
```

## 🔧 Programmatic Usage

You can also import and use these functions in your own Python scripts:

```python
from create_authorized_user import create_authorized_user

# Create single user
create_authorized_user(
    email="newplayer@team.com",
    organization_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    assigned_role="player",
    full_name="Mike Trout",
    authorized_by="admin-user-uuid-here",
    authorization_note="New team member - outfielder"
)
```

```python
from bulk_create_authorized_users import bulk_create_authorized_users

# Create multiple users
users = [
    {
        'email': 'player1@team.com',
        'full_name': 'John Doe',
        'assigned_role': 'player',
        'authorization_note': 'Pitcher'
    },
    {
        'email': 'coach@team.com',
        'full_name': 'Jane Smith',
        'assigned_role': 'coach',
        'authorization_note': 'Head Coach'
    }
]

bulk_create_authorized_users(
    users=users,
    organization_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    authorized_by="admin-user-uuid-here"
)
```

## 📊 Helper Functions

### List Organizations
```python
from create_authorized_user import list_organizations

orgs = list_organizations()
for org in orgs:
    print(f"{org['name']} - {org['id']}")
```

### List Authorized Users
```python
from create_authorized_user import list_authorized_users

# All authorized users
all_users = list_authorized_users()

# For specific organization
org_users = list_authorized_users(organization_id="org-uuid-here")

for user in org_users:
    print(f"{user['email']} - {user['assigned_role']}")
```

### Load Users from CSV
```python
from bulk_create_authorized_users import load_users_from_csv

users = load_users_from_csv('my_roster.csv')
print(f"Loaded {len(users)} users")
```

## ⚠️ Important Notes

1. **Email Validation:**
   - Emails are automatically converted to lowercase
   - Must contain '@' symbol
   - Duplicate emails for same organization are skipped

2. **Role Validation:**
   - Only valid roles are accepted
   - Invalid roles will cause user creation to fail

3. **Organization Check:**
   - Organization must exist before adding users
   - Organization must be active

4. **Duplicate Handling:**
   - If user already exists in `users` table: Skipped
   - If user already authorized for organization: Skipped
   - No duplicates are created

5. **Secrets File:**
   - Scripts require `.streamlit/secrets.toml` file
   - Must have Supabase connection details

## 🎯 Common Workflows

### New Team Setup
```bash
# 1. Create sample CSV
python bulk_create_authorized_users.py --sample

# 2. Edit sample_users.csv with your team roster

# 3. Import all users
python bulk_create_authorized_users.py
# Select: Load from CSV
# File: sample_users.csv
```

### Add Individual Coach/Admin
```bash
python create_authorized_user.py
# Enter coach email and details
# Select appropriate role
```

### Season Roster Update
```bash
# Export current roster, add new players
# Import updated CSV with bulk script
```

## 🔍 Troubleshooting

**"Error: secrets.toml not found"**
- Ensure you're running from project root
- Check that `.streamlit/secrets.toml` exists

**"Organization not found"**
- Verify organization UUID is correct
- Check organization exists and is active

**"User already exists"**
- User already has an account - use admin panel to manage
- Or use different email address

**"Already authorized"**
- User already in authorized_users for this org
- Check authorized users page to see status

**CSV Parsing Errors**
- Ensure CSV has header row
- Check for proper comma separation
- Verify no special characters in emails

