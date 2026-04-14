// Authentication Module
// Handles login, logout, and auth state management

import { firebaseConfig } from './config.js';
import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js';
import {
    getAuth,
    signInWithEmailAndPassword,
    signOut,
    onAuthStateChanged
} from 'https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js';

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Export auth instance for use in other modules
export { auth };

/**
 * Sign in with email and password
 * @param {string} email 
 * @param {string} password 
 * @returns {Promise<UserCredential>}
 */
export async function login(email, password) {
    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        return { success: true, user: userCredential.user };
    } catch (error) {
        console.error('Login error:', error);
        return { success: false, error: getErrorMessage(error.code) };
    }
}

/**
 * Sign out current user
 * @returns {Promise<void>}
 */
export async function logout() {
    try {
        await signOut(auth);
        window.location.href = '/index.html';
    } catch (error) {
        console.error('Logout error:', error);
        throw error;
    }
}

/**
 * Get current authenticated user
 * @returns {User|null}
 */
export function getCurrentUser() {
    return auth.currentUser;
}

/**
 * Wait for auth state to be determined
 * @returns {Promise<User|null>}
 */
export function waitForAuthInit() {
    return new Promise((resolve) => {
        const unsubscribe = onAuthStateChanged(auth, (user) => {
            unsubscribe();
            resolve(user);
        });
    });
}

/**
 * Protect a page - redirect to login if not authenticated
 * Call this on protected pages like dashboard.html
 */
export async function requireAuth() {
    const user = await waitForAuthInit();
    if (!user) {
        window.location.href = '/index.html';
        return null;
    }
    return user;
}

/**
 * Redirect to dashboard if already logged in
 * Call this on the login page
 */
export async function redirectIfAuthenticated() {
    const user = await waitForAuthInit();
    if (user) {
        window.location.href = '/dashboard.html';
    }
}

/**
 * Convert Firebase error codes to user-friendly messages
 * @param {string} errorCode 
 * @returns {string}
 */
function getErrorMessage(errorCode) {
    const errorMessages = {
        'auth/invalid-email': 'Dirección de correo electrónico inválida.',
        'auth/user-disabled': 'Esta cuenta ha sido deshabilitada.',
        'auth/user-not-found': 'No se encontró ninguna cuenta con este correo.',
        'auth/wrong-password': 'Contraseña incorrecta.',
        'auth/invalid-credential': 'Credenciales inválidas. Verifica tu correo y contraseña.',
        'auth/too-many-requests': 'Demasiados intentos fallidos. Intenta más tarde.',
        'auth/network-request-failed': 'Error de red. Verifica tu conexión a internet.',
    };

    return errorMessages[errorCode] || 'Error de autenticación. Intenta nuevamente.';
}
