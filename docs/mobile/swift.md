# Swift library for iOS/macOS

## Buckia Client

The `BuckiaClient` service is the main entry point for the Buckia library. It is used to interact with the Buckia Storage Bucket. The client is initialized with properties for the primary and fallback storage buckets.
To sync with a storage bucket, a token is needed. This requires the user to authenticate with an email/user-id and passkey. The token is stored in the Keychain and used for all requests to the storage bucket. The token is automatically refreshed when it expires. It is stored in the Keychain so it can be used with the web as well.

## Buckia folder structure

|- <user-id>
| | - backup.sqlite
| | - originals
| | - reworked
| | - inbound

The local file structure is managed by the Buckia library. The `user-id` folder is created when the user is created. This folder is used to store a local copy that can be sync'ed 1-to-1 with the user's folder in the Storage Bucket. The `backup.sqlite` file is a backup of the local SQLite database. It is used to restore the local database if needed. The `originals` folder holds the original recording files. The `reworked` folder holds the downscaled recordings for viewing. The `inbound` folder holds the incoming SQLite database diff files used to update the local database. This is used to send requests and shares between users.

The client App uses a local primary SQLite database(in App Support Folder) to store data and downscaled media thumbnails. New recordings are saved under `originals` and referenced in the database. When the App becomes inactive or goes to the background, the App calls the library to back up the database to the `backup.sqlite` in case changes have been made since the last backup. This will be done using APFS Copy-on-Write which is nearly instantanious. It should mean that there is no need to check if changes have been made since the last backup.

The local user folder can be configured to be stored under the App Support folder or the App Documents folder. If the folder isn't present, the other location is checked. If the folder is in the wrong location, it is moved to the correct location.

The `inbound` folder holds incremental changes to the local SQLite database. This is used to send requests and shares between users. These files are used to update the local database with changes from other users. The local DB has a table tracking past applied changes. The files are named using KSUIDs. This allows for quick sorting of files that have to be applied. The table definitions from the incoming DB file is used to adjust the local DB file. Additional tables are used to hold references to the changes.

## Buckia folder syncing

- List the filenames in `inbound` folder within the Storage Bucket. Download only IDs bigger than the last applied ID to the local `inbound` folder.
- Apply the changes to the local SQLite database. Drop applied files as needed to save space.
- Upload the `backup.sqlite` file to the Storage Bucket under the `user-id` folder.
- If enabled, upload new files in the `originals` folder to the Storage Bucket under the `user-id` folder.
- Upload new files in the `reworked` folder to the Storage Bucket under the `user-id` folder.
