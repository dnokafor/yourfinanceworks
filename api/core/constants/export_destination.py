"""
Constants for export destination management.
"""

# Supported export destination types
EXPORT_DESTINATION_TYPES = ['s3', 'azure', 'gcs', 'google_drive', 'local']

# Destination types that support connection testing
TESTABLE_DESTINATION_TYPES = ['s3', 'azure', 'gcs', 'google_drive']

# Destination type labels for UI
DESTINATION_TYPE_LABELS = {
    's3': 'AWS S3',
    'azure': 'Azure Blob Storage',
    'gcs': 'Google Cloud Storage',
    'google_drive': 'Google Drive',
    'local': 'Local File System',
}
