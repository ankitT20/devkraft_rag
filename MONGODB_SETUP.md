# MongoDB Atlas Setup Guide

This guide will help you set up and test MongoDB Atlas for chat history storage.

## Overview

The application now supports storing chat history in MongoDB Atlas with automatic fallback to JSON files. This provides:

- ✅ Persistent cloud storage for chat history
- ✅ Better query performance for large chat histories
- ✅ Automatic failover to JSON files if MongoDB is unavailable
- ✅ Zero-configuration fallback mode

## Setup Steps

### 1. Get Your MongoDB URI

You mentioned you have already created a "ragcluster" on MongoDB Atlas. Your connection string should look like:

```
mongodb+srv://ankit_db_user:PASSWORD@ragcluster.isyht34.mongodb.net/?retryWrites=true
```

**Important:** Replace `PASSWORD` with your actual database user password.

### 2. Configure the Application

Set the `MONGO_URI` environment variable:

**On Windows (Command Prompt):**
```cmd
setx MONGO_URI "mongodb+srv://ankit_db_user:PASSWORD@ragcluster.isyht34.mongodb.net/?retryWrites=true"
```

**On Windows (PowerShell):**
```powershell
[Environment]::SetEnvironmentVariable("MONGO_URI", "mongodb+srv://ankit_db_user:PASSWORD@ragcluster.isyht34.mongodb.net/?retryWrites=true", "User")
```

**On Linux/Mac:**
```bash
export MONGO_URI="mongodb+srv://ankit_db_user:PASSWORD@ragcluster.isyht34.mongodb.net/?retryWrites=true"
```

**Or add to `.env` file:**
```env
MONGO_URI=mongodb+srv://ankit_db_user:PASSWORD@ragcluster.isyht34.mongodb.net/?retryWrites=true
```

### 3. Test the Connection

Run the test script to verify everything is working:

```bash
python test_mongodb_connection.py
```

**Expected Output (Success):**
```
✓ MongoDB Atlas connection successful!
✓ Write operation successful
✓ Read operation successful
✓ Get recent chats successful
✓ All MongoDB tests passed!
```

**Expected Output (Fallback Mode):**
```
⚠️  MongoDB not available - using JSON file fallback
✓ JSON fallback mode is working!
```

## How It Works

### Automatic URI Formatting

The application automatically appends the required parameters to your MongoDB URI:
- `&w=majority` - Write concern for data durability
- `&appName=ragcluster` - Application identifier

So your URI:
```
mongodb+srv://ankit_db_user:PASSWORD@ragcluster.isyht34.mongodb.net/?retryWrites=true
```

Becomes:
```
mongodb+srv://ankit_db_user:PASSWORD@ragcluster.isyht34.mongodb.net/?retryWrites=true&w=majority&appName=ragcluster
```

You don't need to add these manually!

### Storage Strategy

1. **MongoDB Available**: All chat history is stored in MongoDB Atlas
   - Database: `devkraft_rag`
   - Collection: `chat_history`
   - Indexes: `chat_id` (unique), `updated_at` (for sorting)

2. **MongoDB Unavailable**: Automatic fallback to JSON files
   - Location: `user_chat/` folder
   - Format: `{chat_id}.json`
   - Same structure as before

### Streaming Compatibility

The MongoDB integration is fully compatible with the existing streaming functionality. Chat history is saved after each complete response, whether streaming or not.

## Troubleshooting

### Connection Issues

If the test script shows "MongoDB not available", check:

1. **Network Access**: MongoDB Atlas IP whitelist
   - You mentioned adding `0.0.0.0/0` which should allow all IPs
   - Verify in MongoDB Atlas: Network Access → IP Access List

2. **Credentials**: Verify username and password
   - Username: `ankit_db_user`
   - Password: Check your password is correct
   - Special characters in password may need URL encoding

3. **Connection String**: Ensure the URI is correct
   - Cluster name: `ragcluster.isyht34.mongodb.net`
   - Format: `mongodb+srv://...`

4. **Firewall**: Check if your firewall is blocking MongoDB connections
   - MongoDB uses port 27017
   - SRV connections may require port 53 (DNS)

### URL Encoding Passwords

If your password contains special characters, they need to be URL-encoded:

| Character | Encoded |
|-----------|---------|
| @         | %40     |
| :         | %3A     |
| /         | %2F     |
| #         | %23     |
| ?         | %3F     |
| &         | %26     |
| =         | %3D     |

Example:
```
Password: MyP@ss:word
Encoded:  MyP%40ss%3Aword
```

### Verifying Configuration

To check if the environment variable is set:

**Windows Command Prompt:**
```cmd
echo %MONGO_URI%
```

**Windows PowerShell:**
```powershell
$env:MONGO_URI
```

**Linux/Mac:**
```bash
echo $MONGO_URI
```

## Migration from JSON to MongoDB

The application handles both storage methods seamlessly:

1. **Existing JSON Files**: Will continue to be read if MongoDB is unavailable
2. **New Chats**: Will be stored in MongoDB (if available)
3. **No Data Loss**: JSON files are kept as backup even when MongoDB is active

To migrate existing JSON chat history to MongoDB:

1. Ensure MongoDB is connected (test script shows success)
2. Start the application - it will read from JSON files
3. When users interact with old chats, they will be automatically saved to MongoDB

## Performance Considerations

### MongoDB Advantages

- **Scalability**: Better for large numbers of chat sessions
- **Query Performance**: Indexed queries are faster
- **Concurrent Access**: Better handling of simultaneous users
- **Cloud Backup**: Automatic backups in MongoDB Atlas

### JSON Fallback Advantages

- **Simplicity**: No external dependencies
- **Debugging**: Easy to inspect chat files manually
- **Portability**: Can be version controlled or shared easily

## Support

If you encounter issues:

1. Run `python test_mongodb_connection.py` and share the output
2. Check the application logs in `logs/app_logs_YYYYMMDD.log`
3. Verify your MongoDB Atlas dashboard shows the connection attempts

## Related Configuration

Other MongoDB settings in `app/config.py` (can be customized):

```python
mongo_db_name: str = "devkraft_rag"           # Database name
mongo_collection_name: str = "chat_history"    # Collection name
```

To change these, add to `.env`:
```env
MONGO_DB_NAME=my_custom_db
MONGO_COLLECTION_NAME=my_chats
```

---

**Note**: The application works perfectly without MongoDB - the JSON fallback is production-ready. MongoDB is an optional enhancement for scalability and performance.
