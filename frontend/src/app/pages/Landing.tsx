import { useState } from 'react';
import { useNavigate } from 'react-router';
import { motion } from 'motion/react';
import { Github, ArrowRight, Sparkles, Code2, FolderTree, Zap } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { ThemeToggle } from '../components/ThemeToggle';
import { Typewriter } from '../components/Typewriter';
import { useAuth } from '../context/AuthContext';

export function Landing() {
  const [repoUrl, setRepoUrl] = useState('');
  const { isAuthenticated, user, signIn, signOut } = useAuth();
  const navigate = useNavigate();

  const handleAnalyze = () => {
    // Always persist the current URL so /processing can read it
    // regardless of auth state or refresh timing.
    sessionStorage.setItem('pendingRepoUrl', repoUrl);

    if (!isAuthenticated) {
      signIn();
      setTimeout(() => {
        navigate('/processing');
      }, 500);
    } else {
      navigate('/processing');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-accent/10 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-20 left-20 w-[500px] h-[500px] rounded-full blur-3xl"
          style={{
            background: 'radial-gradient(circle, rgba(234, 113, 69, 0.15) 0%, rgba(234, 113, 69, 0.05) 50%, transparent 100%)',
          }}
          animate={{
            x: [0, 120, -80, 0],
            y: [0, -100, 80, 0],
            scale: [1, 1.2, 0.9, 1],
          }}
          transition={{
            duration: 30,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-20 right-20 w-[600px] h-[600px] rounded-full blur-3xl"
          style={{
            background: 'radial-gradient(circle, rgba(234, 113, 69, 0.1) 0%, rgba(234, 113, 69, 0.03) 50%, transparent 100%)',
          }}
          animate={{
            x: [0, -150, 100, 0],
            y: [0, 120, -90, 0],
            scale: [1, 0.8, 1.1, 1],
          }}
          transition={{
            duration: 35,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full blur-3xl"
          style={{
            background: 'radial-gradient(circle, rgba(244, 165, 130, 0.08) 0%, rgba(234, 113, 69, 0.02) 50%, transparent 100%)',
          }}
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 25,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </div>

      {/* Header */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-3"
        >
          <div className="p-2 bg-gradient-to-br from-primary to-primary/80 rounded-xl">
            <Code2 className="w-6 h-6 text-white" />
          </div>
          <span className="text-2xl font-bold bg-gradient-to-r from-foreground to-foreground/60 bg-clip-text text-transparent">
            RepoLens
          </span>
        </motion.div>

        <div className="flex items-center gap-4">
          <ThemeToggle />
          {isAuthenticated ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-3"
            >
              <img
                src={user?.avatar}
                alt={user?.name}
                className="w-10 h-10 rounded-full border-2 border-primary/20"
              />
              <Button variant="ghost" onClick={signOut}>
                Sign Out
              </Button>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <Button onClick={signIn} className="bg-primary hover:bg-primary/90">
                Sign In
              </Button>
            </motion.div>
          )}
        </div>
      </nav>

      {/* Main Content */}
      <div className="relative z-10 max-w-5xl mx-auto px-8 pt-20 pb-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 border border-primary/20 rounded-full mb-8"
          >
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary">AI-Powered Repository Analysis</span>
          </motion.div>

          <h1 className="text-6xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-foreground via-foreground to-foreground/60 bg-clip-text text-transparent">
            <Typewriter words={['Understand', 'Analyze', 'Decode', 'Visualize']} /> Any
            <br />
            <span className="bg-gradient-to-r from-primary via-orange-500 to-primary bg-clip-text text-transparent">
              Codebase Instantly
            </span>
          </h1>

          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-12">
            RepoLens analyzes GitHub repositories to reveal their structure, dependencies, and execution flow in seconds.
          </p>

          {/* Input Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="max-w-2xl mx-auto"
          >
            <div className="flex gap-3 p-2 bg-card border border-border/50 rounded-2xl shadow-2xl backdrop-blur-sm">
              <div className="flex items-center gap-3 flex-1 px-4">
                <Github className="w-5 h-5 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="https://github.com/username/repository"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 text-lg"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && repoUrl.trim()) {
                      handleAnalyze();
                    }
                  }}
                />
              </div>
              <Button
                onClick={handleAnalyze}
                disabled={!repoUrl.trim()}
                className="bg-gradient-to-r from-primary to-orange-500 hover:from-primary/90 hover:to-orange-500/90 text-white px-8 py-6 rounded-xl text-lg shadow-lg shadow-primary/25 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Analyze
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </div>
          </motion.div>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="grid md:grid-cols-3 gap-6 mt-24"
        >
          {[
            {
              icon: FolderTree,
              title: 'Folder Analysis',
              description: 'Understand your repository structure and organization',
              gradient: 'from-orange-500 to-red-500',
            },
            {
              icon: Zap,
              title: 'Entry Detection',
              description: 'Automatically identify starting points and execution flow',
              gradient: 'from-primary to-orange-500',
            },
            {
              icon: Code2,
              title: 'Dependency Map',
              description: 'Visualize how modules and files interact',
              gradient: 'from-orange-400 to-yellow-500',
            },
          ].map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + index * 0.1, duration: 0.6 }}
              whileHover={{ scale: 1.05, y: -5 }}
              className="p-6 bg-card border border-border/50 rounded-2xl backdrop-blur-sm hover:shadow-xl hover:shadow-primary/10 transition-all duration-300 group"
            >
              <div className={`w-12 h-12 bg-gradient-to-br ${feature.gradient} rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
              <p className="text-muted-foreground">{feature.description}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </div>
  );
}