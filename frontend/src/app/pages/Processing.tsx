import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { motion } from 'motion/react';
import { Code2, FolderTree, GitBranch, Zap, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { Progress } from '../components/ui/progress';
import { useAnalysis } from '../context/AnalysisContext';

const steps = [
  { icon: FolderTree, label: 'Fetching repository & scanning tree', duration: 1500 },
  { icon: Code2, label: 'Building dependency graph', duration: 1800 },
  { icon: GitBranch, label: 'Detecting entry point & mapping files', duration: 2000 },
  { icon: Zap, label: 'Generating B3 AI summary & PDF', duration: 1200 },
];

export function Processing() {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const navigate = useNavigate();
  const { setAnalysisData, setError, error } = useAnalysis();

  useEffect(() => {
    const repoUrl = sessionStorage.getItem('pendingRepoUrl');
    let isFetchComplete = false;
    let isAnimationFinished = false;

    if (!repoUrl) {
      setError('No repository URL provided.');
      navigate('/');
      return;
    }

    // 1. Kick off the actual API fetch immediately
    fetch('http://localhost:8000/analyse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ github_url: repoUrl })
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to analyze repository (Server Error)');
        return res.json();
      })
      .then(data => {
        setAnalysisData(data);
        isFetchComplete = true;
        checkCompletion();
      })
      .catch(err => {
        setError(err.message);
        isFetchComplete = true; // Error counts as complete so we stop loader
      });

    // 2. Run the visual progress bar animation
    const totalDuration = steps.reduce((sum, step) => sum + step.duration, 0);
    let elapsed = 0;
    
    const interval = setInterval(() => {
      // If error happened, stop animating
      if (error) {
        clearInterval(interval);
        return;
      }

      elapsed += 50;
      
      // If animation naturally finishes, clamp to 99% until fetch finishes
      let newProgress = (elapsed / totalDuration) * 100;
      if (newProgress >= 100 && !isFetchComplete) {
         newProgress = 99;
      } else if (newProgress >= 100 && isFetchComplete) {
         newProgress = 100;
      }

      setProgress(newProgress);

      // Update current step safely
      let cumulativeDuration = 0;
      for (let i = 0; i < steps.length; i++) {
        cumulativeDuration += steps[i].duration;
        if (elapsed < cumulativeDuration) {
          setCurrentStep(Math.min(i, steps.length - 1));
          break;
        }
      }

      // If both visual and actual fetch are done
      if (elapsed >= totalDuration) {
        isAnimationFinished = true;
        clearInterval(interval);
        checkCompletion();
      }
    }, 50);

    const checkCompletion = () => {
      // Only navigate when both the minimal animation duration AND the API fetch are complete
      if (isAnimationFinished && isFetchComplete) {
        // If we set an error, the user will see it. Maybe don't navigate, or navigate to results and show error there.
        // But for now, just navigate to results where we will handle it.
        setTimeout(() => {
          navigate('/results');
        }, 500);
      }
    };

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-accent/10 flex items-center justify-center p-8 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl"
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.5, 0.3, 0.5],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </div>

      <div className="relative z-10 max-w-2xl w-full">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <motion.div
            animate={{
              rotate: 360,
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "linear",
            }}
            className="inline-block mb-6"
          >
            <div className="w-20 h-20 bg-gradient-to-br from-primary to-orange-500 rounded-2xl flex items-center justify-center">
              <Loader2 className="w-10 h-10 text-white" />
            </div>
          </motion.div>
          
          <h1 className="text-4xl font-bold mb-4">Analyzing Repository</h1>
          <p className="text-muted-foreground text-lg">
            Our AI is diving deep into your codebase...
          </p>
        </motion.div>

        {/* Progress Bar */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mb-12"
        >
          <Progress value={progress} className="h-3 mb-4" />
          <div className="text-center text-sm text-muted-foreground">
            {Math.round(progress)}% Complete
          </div>
        </motion.div>

        {/* Steps */}
        <div className="space-y-4">
          {steps.map((step, index) => {
            const isActive = index === currentStep;
            const isCompleted = index < currentStep;
            const Icon = step.icon;

            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`flex items-center gap-4 p-4 rounded-xl border transition-all duration-300 ${
                  isActive
                    ? 'bg-primary/5 border-primary/50 shadow-lg shadow-primary/10'
                    : isCompleted
                    ? 'bg-card border-border/30'
                    : 'bg-card/50 border-border/20 opacity-50'
                }`}
              >
                <div
                  className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300 ${
                    isActive
                      ? 'bg-gradient-to-br from-primary to-orange-500'
                      : isCompleted
                      ? 'bg-primary/20'
                      : 'bg-muted'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-6 h-6 text-primary" />
                  ) : (
                    <Icon className={`w-6 h-6 ${isActive ? 'text-white' : 'text-muted-foreground'}`} />
                  )}
                </div>
                
                <div className="flex-1">
                  <p className={`font-medium ${isActive ? 'text-foreground' : 'text-muted-foreground'}`}>
                    {step.label}
                  </p>
                </div>

                {isActive && (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  >
                    <Loader2 className="w-5 h-5 text-primary" />
                  </motion.div>
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Fun fact */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-12 text-center text-sm text-muted-foreground"
        >
          <p>💡 Did you know? Most developers spend 60% of their time understanding existing code.</p>
        </motion.div>
      </div>
    </div>
  );
}