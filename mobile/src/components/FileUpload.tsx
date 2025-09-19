import React, { useState } from 'react';
import { logger } from '../utils/logger';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Image,
  ActivityIndicator,
  Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { manipulateAsync, SaveFormat } from 'expo-image-manipulator';
import { useTranslation } from 'react-i18next';

export interface FileData {
  uri: string;
  name: string;
  type: string;
  size?: number;
  originalSize?: number;
  isExisting?: boolean;
  attachmentId?: number;
  uploaded_at?: string;
  compressed?: boolean;
  compressionRatio?: number;
  thumbnailUri?: string;
}

interface FileUploadProps {
  onFilesSelected: (files: FileData[]) => void;
  maxFiles?: number;
  allowedTypes?: string[];
  showCamera?: boolean;
  showGallery?: boolean;
  title?: string;
  maxFileSize?: number; // in MB
  selectedFiles?: FileData[];
  onRemoveFile?: (index: number) => void;
  uploading?: boolean;
  filesToDelete?: Set<number>;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onFilesSelected,
  maxFiles = 5,
  allowedTypes = ['image/jpeg', 'image/png', 'image/jpg'],
  showCamera = true,
  showGallery = true,
  title = 'Upload Files',
  maxFileSize = 10,
  selectedFiles = [],
  onRemoveFile,
  uploading = false,
  filesToDelete = new Set(),
}) => {
  const { t } = useTranslation();
  const [showOptions, setShowOptions] = useState(false);
  const [requestingPermission, setRequestingPermission] = useState(false);
  const [previewFile, setPreviewFile] = useState<FileData | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewError, setPreviewError] = useState(false);
  const [bulkMode, setBulkMode] = useState(false);
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());

  // File Preview Functions
  const handleFilePreview = (file: FileData) => {
    setPreviewFile(file);
    setPreviewError(false); // Reset error state for new preview
    setShowPreview(true);
  };

  // Bulk Operations
  const toggleBulkMode = () => {
    setBulkMode(!bulkMode);
    setSelectedIndices(new Set());
  };

  const toggleFileSelection = (index: number) => {
    const newSelection = new Set(selectedIndices);
    if (newSelection.has(index)) {
      newSelection.delete(index);
    } else {
      newSelection.add(index);
    }
    setSelectedIndices(newSelection);
  };

  const bulkDelete = () => {
    if (selectedIndices.size === 0) return;

    Alert.alert(
      'Delete Files',
      `Are you sure you want to delete ${selectedIndices.size} file(s)?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            const indicesToRemove = Array.from(selectedIndices).sort((a, b) => b - a);
            indicesToRemove.forEach(index => {
              if (onRemoveFile) onRemoveFile(index);
            });
            setSelectedIndices(new Set());
            setBulkMode(false);
          }
        }
      ]
    );
  };

  // Image Compression Function
  const compressImage = async (uri: string, originalSize?: number): Promise<{ uri: string; size: number; compressed: boolean; compressionRatio?: number }> => {
    try {
      // Skip compression for small files
      if (originalSize && originalSize < 500 * 1024) { // Less than 500KB
        return { uri, size: originalSize, compressed: false };
      }

      // Compress the image
      const compressedResult = await manipulateAsync(
        uri,
        [{ resize: { width: 1200 } }], // Resize to max width of 1200px
        {
          compress: 0.8, // 80% quality
          format: SaveFormat.JPEG,
        }
      );

      // Get file info for the compressed image
      const fileInfo = await fetch(compressedResult.uri);
      const blob = await fileInfo.blob();
      const compressedSize = blob.size;

      const compressionRatio = originalSize ? originalSize / compressedSize : undefined;

      return {
        uri: compressedResult.uri,
        size: compressedSize,
        compressed: true,
        compressionRatio,
      };
    } catch (error) {
      logger.error('Image compression failed', error);
      logger.info('Falling back to original image without compression');
      // Return original if compression fails
      return { uri, size: originalSize || 0, compressed: false };
    }
  };

  const requestCameraPermission = async (): Promise<boolean> => {
    try {
      const { status, canAskAgain } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        const message = canAskAgain
          ? 'Camera access is required to take photos. Please grant permission when prompted.'
          : 'Camera access is required to take photos. Please enable it in your device settings.';

        Alert.alert(
          'Camera Permission Required',
          message,
          [
            { text: 'Cancel', style: 'cancel' },
            ...(canAskAgain ? [] : [{ text: 'Settings', onPress: () => {
              // You can add deep linking to settings here if needed
              logger.info('User should go to settings manually');
            }}]),
          ]
        );
        return false;
      }
      return true;
    } catch (error) {
      console.error('Error requesting camera permission:', error);
      Alert.alert(
        'Permission Error',
        'Unable to request camera permission. Please check your device settings.',
        [{ text: 'OK', style: 'default' }]
      );
      return false;
    }
  };

  const requestMediaLibraryPermission = async (): Promise<boolean> => {
    try {
      const { status, canAskAgain } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        const message = canAskAgain
          ? 'Photo library access is required to select images. Please grant permission when prompted.'
          : 'Photo library access is required to select images. Please enable it in your device settings.';

        Alert.alert(
          'Photo Library Permission Required',
          message,
          [
            { text: 'Cancel', style: 'cancel' },
            ...(canAskAgain ? [] : [{ text: 'Settings', onPress: () => {
              logger.info('User should go to settings manually');
            }}]),
          ]
        );
        return false;
      }
      return true;
    } catch (error) {
      console.error('Error requesting media library permission:', error);
      Alert.alert(
        'Permission Error',
        'Unable to request photo library permission. Please check your device settings.',
        [{ text: 'OK', style: 'default' }]
      );
      return false;
    }
  };

  const handleCameraCapture = async () => {
    setRequestingPermission(true);
    try {
      const hasPermission = await requestCameraPermission();
      if (!hasPermission) {
        setRequestingPermission(false);
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ['images'],
        quality: 0.8,
        allowsEditing: true,
        aspect: [4, 3],
        exif: false,
      });

      if (!result.canceled && result.assets.length > 0) {
        const asset = result.assets[0];
        const originalSize = asset.fileSize;

        // Compress image
        let finalUri = asset.uri;
        let finalSize = originalSize || 0;
        let compressed = false;
        let compressionRatio;

        if (asset.mimeType?.startsWith('image/') && asset.uri) {
          try {
            const compressionResult = await compressImage(asset.uri, originalSize);
            finalUri = compressionResult.uri;
            finalSize = compressionResult.size;
            compressed = compressionResult.compressed;
            compressionRatio = compressionResult.compressionRatio;
          } catch (error) {
            console.error('Failed to compress image:', error);
          }
        }

        const fileType = asset.mimeType || 'image/jpeg';

        // Validate file type
        if (!validateFileType(fileType)) {
          Alert.alert(
            'Invalid File Type',
            `File type ${fileType} is not allowed. Allowed types: ${allowedTypes.join(', ')}`
          );
          return;
        }

        const fileData: FileData = {
          uri: finalUri,
          name: asset.fileName || `camera_${Date.now()}.jpg`,
          type: fileType,
          size: finalSize,
          originalSize: compressed ? originalSize : undefined,
          compressed,
          compressionRatio,
        };

        // Check file size
        if (fileData.size && fileData.size > maxFileSize * 1024 * 1024) {
          Alert.alert('File Too Large', `File size must be less than ${maxFileSize}MB`);
          return;
        }

        onFilesSelected([fileData]);
      }
    } catch (error) {
      console.error('Error capturing image:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      Alert.alert(
        'Camera Error',
        `Failed to capture image: ${errorMessage}. Please try again.`,
        [{ text: 'OK', style: 'default' }]
      );
    } finally {
      setRequestingPermission(false);
      setShowOptions(false);
    }
  };

  const handleGallerySelect = async () => {
    setRequestingPermission(true);
    try {
      const hasPermission = await requestMediaLibraryPermission();
      if (!hasPermission) {
        setRequestingPermission(false);
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        quality: 0.8,
        allowsMultipleSelection: maxFiles > 1,
        selectionLimit: maxFiles,
        exif: false,
      });

      if (!result.canceled && result.assets.length > 0) {
        const filesData: FileData[] = await Promise.all(
          result.assets.map(async (asset) => {
            const originalSize = asset.fileSize;
            const fileType = asset.mimeType || 'image/jpeg';

            // Compress images
            let finalUri = asset.uri;
            let finalSize = originalSize || 0;
            let compressed = false;
            let compressionRatio;

            if (asset.mimeType?.startsWith('image/') && asset.uri) {
              try {
                const compressionResult = await compressImage(asset.uri, originalSize);
                finalUri = compressionResult.uri;
                finalSize = compressionResult.size;
                compressed = compressionResult.compressed;
                compressionRatio = compressionResult.compressionRatio;
              } catch (error) {
                console.error('Failed to compress image:', error);
              }
            }

            return {
              uri: finalUri,
              name: asset.fileName || `gallery_${Date.now()}.jpg`,
              type: fileType,
              size: finalSize,
              originalSize: compressed ? originalSize : undefined,
              compressed,
              compressionRatio,
            };
          })
        );

        // Validate file types
        const invalidFiles = filesData.filter(file => !validateFileType(file.type));
        if (invalidFiles.length > 0) {
          const invalidTypes = invalidFiles.map(file => file.type).join(', ');
          Alert.alert(
            'Invalid File Types',
            `Some files have invalid types (${invalidTypes}). Only these types are allowed: ${allowedTypes.join(', ')}`
          );
          return;
        }

        // Check file sizes
        const oversizedFiles = filesData.filter(file =>
          file.size && file.size > maxFileSize * 1024 * 1024
        );

        if (oversizedFiles.length > 0) {
          Alert.alert('Files Too Large', `Some files exceed the ${maxFileSize}MB limit and were not selected.`);
          // Filter out oversized files
          const validFiles = filesData.filter(file =>
            !file.size || file.size <= maxFileSize * 1024 * 1024
          );
          if (validFiles.length > 0) {
            onFilesSelected(validFiles);
          }
        } else {
          onFilesSelected(filesData);
        }
      }
    } catch (error) {
      console.error('Error selecting from gallery:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      Alert.alert(
        'Gallery Error',
        `Failed to select images: ${errorMessage}. Please try again.`,
        [{ text: 'OK', style: 'default' }]
      );
    } finally {
      setRequestingPermission(false);
      setShowOptions(false);
    }
  };

  const handleOpenOptions = () => {
    if (uploading) return;
    setShowOptions(true);
  };

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileTypeIcon = (type: string) => {
    if (type.startsWith('image/')) {
      return 'image-outline';
    }
    return 'document-outline';
  };

  const validateFileType = (fileType: string): boolean => {
    if (allowedTypes.length === 0) return true; // Allow all types if none specified

    return allowedTypes.some(allowedType => {
      if (allowedType.includes('*')) {
        // Handle wildcards like 'image/*'
        const [mainType] = allowedType.split('/');
        return fileType.startsWith(`${mainType}/`);
      }
      return fileType === allowedType;
    });
  };

  return (
    <React.Fragment>
      <View style={styles.container}>
        <Text style={styles.title}>{title}</Text>

        {/* Selected Files Preview */}
        {selectedFiles.length > 0 && (
          <View style={styles.filesList}>
            {selectedFiles.map((file, index) => {
              const isMarkedForDeletion = filesToDelete.has(index);
              return (
                <View
                  key={index}
                  style={[
                    styles.fileItem,
                    bulkMode && selectedIndices.has(index) && styles.fileItemSelected,
                    isMarkedForDeletion && styles.fileItemMarkedForDeletion
                  ]}
                >
                {bulkMode && (
                  <TouchableOpacity
                  style={styles.checkbox}
                  onPress={() => toggleFileSelection(index)}
                >
                  <Ionicons
                    name={selectedIndices.has(index) ? "checkbox" : "square-outline"}
                    size={20}
                    color={selectedIndices.has(index) ? "#10B981" : "#9CA3AF"}
                  />
                </TouchableOpacity>
              )}
              <TouchableOpacity
                style={styles.fileInfo}
                onPress={() => !bulkMode && handleFilePreview(file)}
                disabled={bulkMode}
                accessibilityRole="button"
                accessibilityLabel={`Preview file: ${file.name}`}
                accessibilityHint="Opens a preview of the selected file"
                accessibilityState={{ disabled: bulkMode }}
              >
                <Ionicons
                  name={getFileTypeIcon(file.type)}
                  size={24}
                  color="#6B7280"
                />
                <View style={styles.fileDetails}>
                  <Text style={styles.fileName} numberOfLines={1}>
                    {file.name}
                  </Text>
                  {file.size && (
                    <Text style={styles.fileSize}>
                      {formatFileSize(file.size)}
                      {file.originalSize && file.originalSize !== file.size && (
                        <Text style={styles.compressionText}>
                          {" "}• Compressed {Math.round((1 - file.size / file.originalSize) * 100)}%
                        </Text>
                      )}
                    </Text>
                  )}
                </View>
              </TouchableOpacity>
              {file.uri ? (
                <TouchableOpacity
                  onPress={() => !bulkMode && handleFilePreview(file)}
                  disabled={bulkMode}
                  accessibilityRole="image"
                  accessibilityLabel={`Preview image: ${file.name}`}
                  accessibilityHint="Opens a larger preview of this image"
                  accessibilityState={{ disabled: bulkMode }}
                >
                  <Image source={{ uri: file.uri }} style={styles.filePreview} />
                </TouchableOpacity>
              ) : (
                <TouchableOpacity
                  style={[styles.filePreview, styles.filePreviewPlaceholder]}
                  onPress={() => !bulkMode && handleFilePreview(file)}
                  disabled={bulkMode}
                  accessibilityRole="button"
                  accessibilityLabel={`Preview file: ${file.name} (no preview available)`}
                  accessibilityHint="Opens file information since preview is not available"
                  accessibilityState={{ disabled: bulkMode }}
                >
                  <Ionicons name="document-outline" size={24} color="#6B7280" />
                </TouchableOpacity>
              )}
              {onRemoveFile && !bulkMode && (
                <TouchableOpacity
                  style={styles.removeButton}
                  onPress={() => onRemoveFile(index)}
                  disabled={uploading}
                  accessibilityRole="button"
                  accessibilityLabel={`Remove file: ${file.name}`}
                  accessibilityHint="Removes this file from the selection"
                  accessibilityState={{ disabled: uploading }}
                >
                  <Ionicons name="close-circle" size={20} color="#EF4444" />
                </TouchableOpacity>
              )}

              {/* Deletion indicator */}
              {isMarkedForDeletion && (
                <View style={styles.deletionIndicator}>
                  <Ionicons name="trash-outline" size={16} color="#EF4444" />
                  <Text style={styles.deletionText}>Will be deleted when saved</Text>
                </View>
              )}
            </View>
              );
            })}
        </View>
      )}

      {/* Bulk Operations Toolbar */}
      {selectedFiles.length > 0 && (
        <View style={styles.bulkToolbar}>
          <TouchableOpacity
            style={[styles.bulkButton, bulkMode && styles.bulkButtonActive]}
            onPress={toggleBulkMode}
            accessibilityRole="button"
            accessibilityLabel={bulkMode ? "Exit bulk selection mode" : "Enter bulk selection mode"}
            accessibilityHint={bulkMode ? "Cancels selection and returns to normal view" : "Allows selecting multiple files for bulk operations"}
            accessibilityState={{ selected: bulkMode }}
          >
            <Ionicons
              name={bulkMode ? "close" : "checkmark-circle-outline"}
              size={20}
              color={bulkMode ? "#FFFFFF" : "#6B7280"}
            />
            <Text style={[styles.bulkButtonText, bulkMode && styles.bulkButtonTextActive]}>
              {bulkMode ? "Cancel" : "Select"}
            </Text>
          </TouchableOpacity>

          {bulkMode && selectedIndices.size > 0 && (
            <TouchableOpacity
              style={[styles.bulkButton, styles.bulkButtonDelete]}
              onPress={bulkDelete}
              accessibilityRole="button"
              accessibilityLabel={`Delete ${selectedIndices.size} selected files`}
              accessibilityHint="Permanently removes the selected files from the list"
            >
              <Ionicons name="trash" size={20} color="#FFFFFF" />
              <Text style={[styles.bulkButtonText, styles.bulkButtonTextActive]}>
                Delete ({selectedIndices.size})
              </Text>
            </TouchableOpacity>
          )}
        </View>
      )}

      {/* Upload Button */}
      <TouchableOpacity
        style={[
          styles.uploadButton,
          uploading && styles.uploadButtonDisabled,
          selectedFiles.length >= maxFiles && styles.uploadButtonDisabled
        ]}
        onPress={handleOpenOptions}
        disabled={uploading || selectedFiles.length >= maxFiles}
        accessibilityRole="button"
        accessibilityLabel={uploading ? "Uploading files" : "Select files to upload"}
        accessibilityHint={
          selectedFiles.length === 0
            ? "Opens menu to choose files from camera or gallery"
            : `Add more files. Currently ${selectedFiles.length} of ${maxFiles} selected`
        }
        accessibilityState={{
          disabled: uploading || selectedFiles.length >= maxFiles,
          busy: uploading
        }}
      >
        {uploading ? (
          <ActivityIndicator size="small" color="#FFFFFF" />
        ) : (
          <>
            <Ionicons name="cloud-upload-outline" size={20} color="#FFFFFF" />
            <Text style={styles.uploadButtonText}>
              {selectedFiles.length === 0
                ? 'Select Files'
                : `Add More (${selectedFiles.length}/${maxFiles})`
              }
            </Text>
          </>
        )}
      </TouchableOpacity>

      {/* Upload Options Modal */}
      <Modal
        visible={showOptions}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowOptions(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Choose Upload Method</Text>

            {showCamera && (
              <TouchableOpacity
                style={styles.modalOption}
                onPress={handleCameraCapture}
                disabled={requestingPermission}
                accessibilityRole="button"
                accessibilityLabel="Take photo with camera"
                accessibilityHint="Opens camera to capture a new photo"
                accessibilityState={{ disabled: requestingPermission, busy: requestingPermission }}
              >
                {requestingPermission ? (
                  <ActivityIndicator size="small" color="#3B82F6" />
                ) : (
                  <Ionicons name="camera-outline" size={24} color="#3B82F6" />
                )}
                <Text style={styles.modalOptionText}>Take Photo</Text>
              </TouchableOpacity>
            )}

            {showGallery && (
              <TouchableOpacity
                style={styles.modalOption}
                onPress={handleGallerySelect}
                disabled={requestingPermission}
                accessibilityRole="button"
                accessibilityLabel={`Select from gallery ${maxFiles > 1 ? '(multiple files allowed)' : '(single file)'}`}
                accessibilityHint="Opens photo gallery to select existing photos"
                accessibilityState={{ disabled: requestingPermission, busy: requestingPermission }}
              >
                {requestingPermission ? (
                  <ActivityIndicator size="small" color="#3B82F6" />
                ) : (
                  <Ionicons name="images-outline" size={24} color="#3B82F6" />
                )}
                <Text style={styles.modalOptionText}>
                  {maxFiles > 1 ? 'Select from Gallery' : 'Choose from Gallery'}
                </Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity
              style={styles.modalCancel}
              onPress={() => setShowOptions(false)}
              accessibilityRole="button"
              accessibilityLabel="Cancel file selection"
              accessibilityHint="Closes the upload options menu"
            >
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
      </View>

      {/* File Preview Modal */}
    <Modal
      visible={showPreview}
      animationType="fade"
      transparent={true}
      onRequestClose={() => setShowPreview(false)}
    >
      <View style={styles.previewModalOverlay}>
        <View style={styles.previewModalContent}>
          <View style={styles.previewHeader}>
            <Text style={styles.previewTitle} numberOfLines={1}>
              {previewFile?.name}
            </Text>
            <TouchableOpacity
              onPress={() => setShowPreview(false)}
              style={styles.previewCloseButton}
            >
              <Ionicons name="close" size={24} color="#6B7280" />
            </TouchableOpacity>
          </View>

          <View style={styles.previewBody}>
            {previewFile?.uri && !previewError ? (
              <Image
                source={{ uri: previewFile.uri }}
                style={styles.previewImage}
                resizeMode="contain"
                onError={() => {
                  // Handle image load errors (e.g., attachment was deleted)
                  logger.warn('Failed to load preview image, attachment may have been deleted');
                  setPreviewError(true);
                }}
              />
            ) : (
              <View style={styles.previewPlaceholder}>
                <Ionicons
                  name={previewError ? "alert-circle-outline" : "document-outline"}
                  size={48}
                  color={previewError ? "#EF4444" : "#9CA3AF"}
                />
                <Text style={styles.previewPlaceholderText}>
                  {previewError
                    ? "Preview not available\n(File may have been deleted)"
                    : "Preview not available"
                  }
                </Text>
              </View>
            )}
          </View>

          {previewFile && (
            <View style={styles.previewFooter}>
              <View style={styles.previewInfo}>
                <Text style={styles.previewInfoText}>
                  Type: {previewFile.type}
                </Text>
                {previewFile.size && (
                  <Text style={styles.previewInfoText}>
                    Size: {formatFileSize(previewFile.size)}
                    {previewFile.originalSize && previewFile.originalSize !== previewFile.size && (
                      <Text style={styles.compressionText}>
                        {" "}• Compressed {Math.round((1 - previewFile.size / previewFile.originalSize) * 100)}%
                      </Text>
                    )}
                  </Text>
                )}
                {previewFile.uploaded_at && (
                  <Text style={styles.previewInfoText}>
                    Uploaded: {new Date(previewFile.uploaded_at).toLocaleDateString()}
                  </Text>
                )}
              </View>
            </View>
          )}
        </View>
      </View>
    </Modal>
    </React.Fragment>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 20,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
  },
  filesList: {
    marginBottom: 12,
  },
  fileItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  fileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  fileDetails: {
    flex: 1,
    marginLeft: 12,
  },
  fileName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 2,
  },
  fileSize: {
    fontSize: 12,
    color: '#6B7280',
  },
  filePreview: {
    width: 40,
    height: 40,
    borderRadius: 4,
    marginLeft: 8,
  },
  filePreviewPlaceholder: {
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  removeButton: {
    padding: 4,
    marginLeft: 8,
  },
  uploadButton: {
    backgroundColor: '#3B82F6',
    borderRadius: 8,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  uploadButtonDisabled: {
    backgroundColor: '#9CA3AF',
  },
  uploadButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '500',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    width: '80%',
    maxWidth: 300,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 20,
    textAlign: 'center',
  },
  modalOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 12,
    borderRadius: 8,
    marginBottom: 12,
    backgroundColor: '#F3F4F6',
    gap: 12,
  },
  modalOptionText: {
    fontSize: 16,
    color: '#374151',
    fontWeight: '500',
  },
  modalCancel: {
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  modalCancelText: {
    fontSize: 16,
    color: '#6B7280',
    fontWeight: '500',
  },

  // Bulk Operations Styles
  bulkToolbar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  bulkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
    gap: 6,
  },
  bulkButtonActive: {
    backgroundColor: '#10B981',
  },
  bulkButtonDelete: {
    backgroundColor: '#EF4444',
  },
  bulkButtonText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  bulkButtonTextActive: {
    color: '#FFFFFF',
  },

  // File Item Selection Styles
  fileItemSelected: {
    backgroundColor: '#EFF6FF',
    borderColor: '#3B82F6',
    borderWidth: 1,
  },
  checkbox: {
    padding: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Compression Text Style
  compressionText: {
    color: '#10B981',
    fontWeight: '600',
  },

  // Preview Modal Styles
  previewModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  previewModalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    width: '90%',
    maxHeight: '80%',
    overflow: 'hidden',
  },
  previewHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  previewTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    flex: 1,
    marginRight: 12,
  },
  previewCloseButton: {
    padding: 4,
  },
  previewBody: {
    minHeight: 300,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  previewImage: {
    width: '100%',
    height: 300,
    borderRadius: 8,
  },
  previewPlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  previewPlaceholderText: {
    fontSize: 16,
    color: '#9CA3AF',
    marginTop: 12,
    textAlign: 'center',
  },
  previewFooter: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  previewInfo: {
    gap: 4,
  },
  previewInfoText: {
    fontSize: 14,
    color: '#6B7280',
  },
  fileItemMarkedForDeletion: {
    borderColor: '#EF4444',
    borderWidth: 2,
    backgroundColor: '#FEF2F2',
  },
  deletionIndicator: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#EF4444',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  deletionText: {
    fontSize: 10,
    color: '#FFFFFF',
    fontWeight: '600',
  },
});

export default FileUpload;
