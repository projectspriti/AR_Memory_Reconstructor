# MongoDB Atlas Setup Guide

## Step 1: Create MongoDB Atlas Account

1. Go to https://www.mongodb.com/atlas
2. Click "Try Free" 
3. Sign up with email or Google account

## Step 2: Create a Cluster

1. Choose "M0 Sandbox" (Free tier)
2. Select a cloud provider (AWS recommended)
3. Choose a region close to you
4. Click "Create Cluster"
5. Wait 1-3 minutes for cluster creation

## Step 3: Create Database User

1. Go to "Database Access" in left sidebar
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Enter username and password (save these!)
5. Set privileges to "Read and write to any database"
6. Click "Add User"

## Step 4: Configure Network Access

1. Go to "Network Access" in left sidebar
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (for development)
4. Click "Confirm"

## Step 5: Get Connection String

1. Go to "Clusters" in left sidebar
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Select "Python" and version "3.6 or later"
5. Copy the connection string

## Step 6: Update Backend Configuration

1. Open `backend/.env` file
2. Replace the MONGODB_URI with your Atlas connection string
3. Replace `<password>` with your database user password
4. Replace `<dbname>` with `ar_memory_reconstructor`

Example:
```
MONGODB_URI=mongodb+srv://myuser:mypassword@cluster0.abc123.mongodb.net/ar_memory_reconstructor?retryWrites=true&w=majority
```

## Step 7: Test Connection

```cmd
cd backend
venv\Scripts\activate
python setup_mongodb.py
```

If successful, you'll see:
```
✓ Connected to MongoDB
Setting up collections...
✓ Sessions collection
✓ Results collection  
✓ Processing logs collection
✓ MongoDB setup complete!
```

## Troubleshooting

**Connection timeout:**
- Check network access settings
- Ensure IP address is whitelisted

**Authentication failed:**
- Verify username/password in connection string
- Check database user permissions

**DNS resolution:**
- Try using a different network
- Check firewall settings