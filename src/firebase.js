// Firebase Configuration & Services — Trinetra Drishti AI
import { initializeApp, getApps, getApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { 
  getAuth, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut,
  GoogleAuthProvider,
  signInWithPopup,
  onAuthStateChanged
} from "firebase/auth";
import { 
  getFirestore, 
  collection, 
  doc,
  setDoc,
  getDoc,
  addDoc, 
  query, 
  orderBy, 
  getDocs, 
  serverTimestamp 
} from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyC3Alp0HzH3c_bR0JUCFTQylOJCtCsbCcQ",
  authDomain: "trinetra-drishti-ai.firebaseapp.com",
  projectId: "trinetra-drishti-ai",
  storageBucket: "trinetra-drishti-ai.firebasestorage.app",
  messagingSenderId: "302118304441",
  appId: "1:302118304441:web:404042bc6a44f99357f968",
  measurementId: "G-L6WX8L3YWZ"
};

// Initialize Firebase App
const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();

let analyticsInstance = null;
if (typeof window !== "undefined") {
  try {
    analyticsInstance = getAnalytics(app);
  } catch (e) {
    console.warn("Analytics notice:", e);
  }
}

export const analytics = analyticsInstance;
export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();

// Friendly error message mapping for Firebase Auth error codes
function formatAuthError(error) {
  if (!error) return "An unknown authentication error occurred.";
  const code = error.code || error.message || "";
  
  if (code.includes("auth/internal-error")) {
    return "Firebase Internal Error: Make sure Email/Password & Google Sign-In providers are enabled in Firebase Console (Authentication > Sign-in method).";
  }
  if (code.includes("auth/invalid-credential") || code.includes("auth/wrong-password") || code.includes("auth/user-not-found")) {
    return "Invalid email or password. Click 'Create Account' above if you need a new account.";
  }
  if (code.includes("auth/email-already-in-use")) {
    return "This email is already registered. Please sign in instead.";
  }
  if (code.includes("auth/weak-password")) {
    return "Password is too weak. Please use at least 6 characters.";
  }
  if (code.includes("auth/popup-closed-by-user")) {
    return "Google Sign-In popup was closed before completing.";
  }
  if (code.includes("auth/unauthorized-domain")) {
    return "Domain not authorized in Firebase Console (Authentication > Settings > Authorized Domains).";
  }
  return error.message || "Authentication failed. Check your Firebase Console configuration.";
}

// Save or Update User Profile in Firestore
export async function saveUserProfileToFirestore(user, role = "Senior Forensic Lead") {
  if (!user || !user.uid) return;
  try {
    const userRef = doc(db, "users", user.uid);
    const profileData = {
      uid: user.uid,
      email: user.email || "",
      displayName: user.displayName || user.email?.split("@")[0] || "Officer",
      photoURL: user.photoURL || null,
      role: role,
      authProvider: user.providerData?.[0]?.providerId || "password",
      lastLoginAt: serverTimestamp(),
      updatedAt: new Date().toISOString()
    };
    await setDoc(userRef, profileData, { merge: true });
    return profileData;
  } catch (err) {
    console.warn("Could not write user profile to Firestore:", err);
  }
}

// Fetch User Profile from Firestore
export async function fetchUserProfileFromFirestore(userId) {
  if (!userId) return null;
  try {
    const userRef = doc(db, "users", userId);
    const docSnap = await getDoc(userRef);
    if (docSnap.exists()) {
      return docSnap.data();
    }
  } catch (err) {
    console.warn("Could not fetch user profile from Firestore:", err);
  }
  return null;
}

// ─── AUTHENTICATION HELPERS ──────────────────────────────────────────────────

export async function loginWithEmail(email, password, role) {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    await saveUserProfileToFirestore(user, role);
    await logUserAudit(user.uid, user.email, "LOGIN", "System Auth", "User logged in with Email & Password", "S0", "Desk S0", "Nominal", "AUTH-001");
    return { success: true, user };
  } catch (error) {
    return { success: false, error: formatAuthError(error) };
  }
}

export async function registerWithEmail(email, password, role) {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    await saveUserProfileToFirestore(user, role);
    await logUserAudit(user.uid, user.email, "REGISTER", "System Auth", "New user registered via Firebase Auth", "S0", "Desk S0", "Nominal", "REG-001");
    return { success: true, user };
  } catch (error) {
    return { success: false, error: formatAuthError(error) };
  }
}

export async function loginWithGoogle(role) {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;
    await saveUserProfileToFirestore(user, role);
    await logUserAudit(user.uid, user.email, "GOOGLE_LOGIN", "Google OAuth", "User logged in via Google OAuth", "S0", "Desk S0", "Nominal", "OAUTH-001");
    return { success: true, user };
  } catch (error) {
    return { success: false, error: formatAuthError(error) };
  }
}

export async function logoutUser() {
  try {
    const currentUser = auth.currentUser;
    if (currentUser) {
      await logUserAudit(currentUser.uid, currentUser.email, "LOGOUT", "System Auth", "User logged out of session", "S0", "Desk S0", "Nominal", "OUT-001");
    }
    await signOut(auth);
  } catch (error) {
    console.warn("Sign out error:", error);
  }
}

// ─── FIRESTORE ANOMALY AUDIT LOGS ───────────────────────────────────────────

export async function logUserAudit(
  userId, 
  userEmail, 
  action, 
  operatorId = "System Auth",
  anomalyDetails = "", 
  zoneId = "S4", 
  deskId = "Desk S4", 
  severity = "High",
  checksum = "7f83b165...e9a4"
) {
  if (!userId) return;
  try {
    const userLogsRef = collection(db, "users", userId, "audit_logs");
    const logData = {
      userId,
      userEmail,
      action,
      operatorId: operatorId || userEmail?.split('@')[0] || "Forensic Officer",
      anomaly: anomalyDetails || action,
      details: anomalyDetails || action,
      zoneId: zoneId || "S4",
      deskId: deskId || "Desk S4",
      severity: severity || "High",
      checksum: checksum || `SHA256-${Date.now().toString(16)}`,
      timestamp: new Date().toISOString(),
      createdAt: serverTimestamp(),
      userAgent: navigator.userAgent
    };
    await addDoc(userLogsRef, logData);
    return logData;
  } catch (err) {
    console.warn("Could not write anomaly log to Firestore:", err);
  }
}

export async function getUserAuditLogs(userId) {
  if (!userId) return [];
  try {
    const userLogsRef = collection(db, "users", userId, "audit_logs");
    const q = query(userLogsRef, orderBy("createdAt", "desc"));
    const snapshot = await getDocs(q);
    return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
  } catch (err) {
    console.warn("Could not fetch user audit logs from Firestore:", err);
    return [];
  }
}

export { onAuthStateChanged };
