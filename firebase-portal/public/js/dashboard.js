// Dashboard Module
// Handles download functionality and analytics

import { firebaseConfig } from './config.js';
import { auth, getCurrentUser } from './auth.js';
import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js';
import { getStorage, ref, getDownloadURL } from 'https://www.gstatic.com/firebasejs/9.22.0/firebase-storage.js';
import { getFirestore, collection, addDoc, serverTimestamp } from 'https://www.gstatic.com/firebasejs/9.22.0/firebase-firestore.js';

// Initialize Firebase services
const app = initializeApp(firebaseConfig);
const storage = getStorage(app);
const db = getFirestore(app);

/**
 * Get download URL for Galt release from Firebase Storage
 * @param {string} filePath - Path to file in Storage (e.g., 'releases/galt_latest.zip')
 * @returns {Promise<string>} Download URL
 */
export async function getGaltDownloadURL(filePath = 'releases/galt_latest.zip') {
    try {
        const fileRef = ref(storage, filePath);
        const downloadURL = await getDownloadURL(fileRef);
        return { success: true, url: downloadURL };
    } catch (error) {
        console.error('Error getting download URL:', error);
        return {
            success: false,
            error: 'No se pudo obtener el enlace de descarga. Contacta al administrador.'
        };
    }
}

/**
 * Log download event to Firestore
 * @param {string} fileName - Name of downloaded file
 * @param {string} downloadURL - URL used for download
 */
export async function logDownload(fileName, downloadURL) {
    try {
        const user = getCurrentUser();
        if (!user) {
            console.warn('No user logged in, skipping download log');
            return;
        }

        await addDoc(collection(db, 'downloads'), {
            userId: user.uid,
            userEmail: user.email,
            fileName: fileName,
            downloadURL: downloadURL,
            timestamp: serverTimestamp(),
            userAgent: navigator.userAgent,
            platform: navigator.platform
        });

        console.log('Download logged successfully');
    } catch (error) {
        console.error('Error logging download:', error);
        // Non-critical error, don't block download
    }
}

/**
 * Handle download button click
 * Gets download URL, logs event, and initiates download
 */
export async function handleDownload() {
    const downloadBtn = document.getElementById('download-btn');
    const errorMsg = document.getElementById('download-error');

    if (!downloadBtn) return;

    // Show loading state
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = '<span class="animate-spin inline-block mr-2">⏳</span> Preparando descarga...';

    // Clear previous errors
    if (errorMsg) errorMsg.classList.add('hidden');

    try {
        // Get download URL from Firebase Storage
        const result = await getGaltDownloadURL();

        if (!result.success) {
            throw new Error(result.error);
        }

        // Log the download event
        await logDownload('galt_latest.zip', result.url);

        // Initiate download
        window.open(result.url, '_blank');

        // Show success feedback
        downloadBtn.innerHTML = '✓ Descarga iniciada';
        setTimeout(() => {
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = '⬇️ Descargar Galt v0.1';
        }, 3000);

    } catch (error) {
        console.error('Download failed:', error);

        // Show error message
        if (errorMsg) {
            errorMsg.textContent = error.message;
            errorMsg.classList.remove('hidden');
        }

        // Reset button
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = '⬇️ Descargar Galt v0.1';
    }
}

/**
 * Display user information on dashboard
 */
export function displayUserInfo() {
    const user = getCurrentUser();
    if (!user) return;

    const userEmailElement = document.getElementById('user-email');
    if (userEmailElement) {
        userEmailElement.textContent = user.email;
    }
}
