from motor.motor_asyncio import AsyncIOMotorClient

# Replace with your MongoDB URI
MONGO_URI = "MONGODB_URL"

# Connect to MongoDB
client = AsyncIOMotorClient(MONGO_URI)
db = client["zulibot"]
users_collection = db["users"]
groups_collection = db["groups"]  # Separate collection for groups

async def add_user(user_id, username, language="en", other_settings=None):
    """
    Adds or updates a user in the database.
    """
    if other_settings is None:
        other_settings = {}

    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"username": username, "language": language, "other_settings": other_settings}},
        upsert=True
    )

# Function to get user data (including language and other information)
async def get_user(user_id, username=None):
    """
    Retrieves full user data, including language and other data.
    """
    user = await users_collection.find_one({"user_id": user_id})
    
    if user:
        return {
            "user_id": user.get("user_id"),
            "username": user.get("username"),
            "language": user.get("language", "en"),  # Default to 'en'
            "other_settings": user.get("other_settings", {})
        }

    return {
        "user_id": user_id,
        "username": username,
        "language": "en",  # Default to 'en' for new users
        "other_settings": {}
    }

# Function to get group data (including language and other information)
async def get_group(group_id):
    """
    Retrieves full group data, including language and other settings.
    """
    group = await groups_collection.find_one({"group_id": group_id})
    
    if group:
        return {
            "group_id": group.get("group_id"),
            "language": group.get("language", "en"),  # Default to 'en'
            "other_settings": group.get("other_settings", {})
        }
    
    return {
        "group_id": group_id,
        "language": "en",  # Default to 'en' for new groups
        "other_settings": {}
    }

# Function to add/update group data (language and other settings)
async def add_group(group_id, language="en", other_settings=None):
    """
    Adds or updates group data in the database.
    """
    if other_settings is None:
        other_settings = {}

    await groups_collection.update_one(
        {"group_id": group_id},
        {"$set": {"language": language, "other_settings": other_settings}},
        upsert=True
    )
