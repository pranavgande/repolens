# mock_data/mock_repo.py

"""
This module simulates what the GitHub API would return when you call
GET /repos/{owner}/{repo}/contents and recursively read each file.

In your real implementation, this dict gets populated by your GitHub
fetcher. For now, we hardcode it so the parser pipeline can run
completely standalone.

The keys are repo-relative file paths (always forward slashes).
The values are raw source code as bytes — exactly what you'd get from
the GitHub API's file content endpoint after base64-decoding.
"""

MOCK_REPO_FILES: dict[str, bytes] = {

    # ── Entry point ──────────────────────────────────────────────────────
    "server.js": b"""
const express = require('express');
const connectDB = require('./config/db.config');
const authRoutes = require('./routes/auth.routes');
const userRoutes = require('./routes/user.routes');

const app = express();
connectDB();

app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);

app.listen(3000, () => console.log('Server running on port 3000'));
""",

    # ── Config ────────────────────────────────────────────────────────────
    "config/db.config.js": b"""
const mongoose = require('mongoose');

const connectDB = async () => {
    await mongoose.connect(process.env.MONGO_URI);
    console.log('MongoDB connected');
};

module.exports = connectDB;
""",

    # ── Routes ───────────────────────────────────────────────────────────
    "routes/auth.routes.js": b"""
const express = require('express');
const router = express.Router();
const authController = require('../controllers/auth.controller');
const authMiddleware = require('../middleware/auth.middleware');

router.post('/login', authController.login);
router.post('/register', authController.register);
router.get('/profile', authMiddleware.verifyToken, authController.getProfile);

module.exports = router;
""",

    "routes/user.routes.js": b"""
const express = require('express');
const router = express.Router();
const userController = require('../controllers/user.controller');
const authMiddleware = require('../middleware/auth.middleware');

router.get('/', authMiddleware.verifyToken, userController.getAllUsers);
router.delete('/:id', authMiddleware.verifyToken, userController.deleteUser);

module.exports = router;
""",

    # ── Controllers ──────────────────────────────────────────────────────
    "controllers/auth.controller.js": b"""
const authService = require('../services/auth.service');

exports.login = async (req, res) => {
    const result = await authService.loginUser(req.body);
    res.json(result);
};

exports.register = async (req, res) => {
    const result = await authService.registerUser(req.body);
    res.json(result);
};

exports.getProfile = async (req, res) => {
    const user = await authService.getUserById(req.user.id);
    res.json(user);
};
""",

    "controllers/user.controller.js": b"""
const userService = require('../services/user.service');

exports.getAllUsers = async (req, res) => {
    const users = await userService.findAllUsers();
    res.json(users);
};

exports.deleteUser = async (req, res) => {
    await userService.removeUser(req.params.id);
    res.status(204).send();
};
""",

    # ── Services ─────────────────────────────────────────────────────────
    "services/auth.service.js": b"""
const UserModel = require('../models/user.model');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

exports.loginUser = async ({ email, password }) => {
    const user = await UserModel.findByEmail(email);
    const isValid = await bcrypt.compare(password, user.passwordHash);
    if (!isValid) throw new Error('Invalid credentials');
    return jwt.sign({ id: user._id }, process.env.JWT_SECRET);
};

exports.registerUser = async (data) => {
    const hash = await bcrypt.hash(data.password, 10);
    return UserModel.create({ ...data, passwordHash: hash });
};

exports.getUserById = async (id) => {
    return UserModel.findById(id);
};
""",

    "services/user.service.js": b"""
const UserModel = require('../models/user.model');

exports.findAllUsers = async () => {
    return UserModel.find({});
};

exports.removeUser = async (id) => {
    return UserModel.findByIdAndDelete(id);
};
""",

    # ── Models ───────────────────────────────────────────────────────────
    "models/user.model.js": b"""
const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
    name: String,
    email: { type: String, unique: true },
    passwordHash: String,
    role: { type: String, default: 'user' },
});

module.exports = mongoose.model('User', userSchema);
""",

    # ── Middleware ────────────────────────────────────────────────────────
    "middleware/auth.middleware.js": b"""
const jwt = require('jsonwebtoken');

exports.verifyToken = (req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) return res.status(401).json({ error: 'No token' });
    req.user = jwt.verify(token, process.env.JWT_SECRET);
    next();
};
""",
}