import { useState } from 'react';
import { motion } from 'motion/react';
import { useNavigate } from 'react-router';
import {
  ArrowLeft,
  FolderTree,
  Zap,
  GitBranch,
  Star,
  TrendingUp,
  BookOpen,
  Code2,
  Database,
  Shield,
  Box,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { ThemeToggle } from '../components/ThemeToggle';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Separator } from '../components/ui/separator';
import { demoResults } from '../data/demoResults';

export function Results() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('m1');

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-accent/5">
      {/* Header */}
      <nav className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/')}
              className="hover:bg-primary/10"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-primary to-orange-500 rounded-lg">
                <Code2 className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="font-semibold">Repository Analysis</h2>
                <p className="text-sm text-muted-foreground">username/repository</p>
              </div>
            </div>
          </div>
          <ThemeToggle />
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-6 h-auto p-1 bg-muted/30 backdrop-blur-sm">
              <TabsTrigger
                value="m1"
                className="flex flex-col items-center gap-2 py-3 data-[state=active]:bg-primary data-[state=active]:text-white"
              >
                <FolderTree className="w-5 h-5" />
                <span className="text-xs font-medium">M1: Structure</span>
              </TabsTrigger>
              <TabsTrigger
                value="m2"
                className="flex flex-col items-center gap-2 py-3 data-[state=active]:bg-primary data-[state=active]:text-white"
              >
                <Zap className="w-5 h-5" />
                <span className="text-xs font-medium">M2: Entry Point</span>
              </TabsTrigger>
              <TabsTrigger
                value="m3"
                className="flex flex-col items-center gap-2 py-3 data-[state=active]:bg-primary data-[state=active]:text-white"
              >
                <GitBranch className="w-5 h-5" />
                <span className="text-xs font-medium">M3: Dependencies</span>
              </TabsTrigger>
              <TabsTrigger
                value="b1"
                className="flex flex-col items-center gap-2 py-3 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-orange-500 data-[state=active]:text-white"
              >
                <Star className="w-5 h-5" />
                <span className="text-xs font-medium">B1: Critical Files</span>
              </TabsTrigger>
              <TabsTrigger
                value="b2"
                className="flex flex-col items-center gap-2 py-3 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-orange-500 data-[state=active]:text-white"
              >
                <TrendingUp className="w-5 h-5" />
                <span className="text-xs font-medium">B2: Exec Flow</span>
              </TabsTrigger>
              <TabsTrigger
                value="b3"
                className="flex flex-col items-center gap-2 py-3 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-orange-500 data-[state=active]:text-white"
              >
                <BookOpen className="w-5 h-5" />
                <span className="text-xs font-medium">B3: Summary</span>
              </TabsTrigger>
            </TabsList>

            {/* M1: Folder Structure */}
            <TabsContent value="m1" className="space-y-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Card className="border-primary/20 shadow-xl shadow-primary/5">
                  <CardHeader>
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-gradient-to-br from-primary to-orange-500 rounded-xl">
                        <FolderTree className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-2xl">Folder Structure Analysis</CardTitle>
                        <CardDescription>
                          Understanding the repository organization and directory hierarchy
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {demoResults.folderStructure.structure.map((folder, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="space-y-3"
                      >
                        <div className="flex items-start gap-3 p-4 bg-muted/30 rounded-lg border border-border/50 hover:bg-muted/50 transition-colors">
                          <Box className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                          <div className="flex-1">
                            <code className="text-sm font-mono font-semibold text-primary">
                              {folder.path}
                            </code>
                            <p className="text-sm text-muted-foreground mt-1">
                              {folder.description}
                            </p>
                          </div>
                        </div>
                        {folder.children && (
                          <div className="ml-8 space-y-2">
                            {folder.children.map((child, childIndex) => (
                              <div
                                key={childIndex}
                                className="flex items-start gap-3 p-3 bg-accent/20 rounded-lg border border-border/30"
                              >
                                <Box className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                  <code className="text-sm font-mono font-medium text-orange-600 dark:text-orange-400">
                                    {child.path}
                                  </code>
                                  <p className="text-xs text-muted-foreground mt-1">
                                    {child.description}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>

            {/* M2: Entry Point */}
            <TabsContent value="m2" className="space-y-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Card className="border-primary/20 shadow-xl shadow-primary/5">
                  <CardHeader>
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-gradient-to-br from-primary to-orange-500 rounded-xl">
                        <Zap className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-2xl">Entry Point Detection</CardTitle>
                        <CardDescription>
                          Identified starting point and initial execution flow
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="flex items-center gap-3 p-4 bg-gradient-to-r from-primary/10 to-orange-500/10 rounded-lg border border-primary/30">
                      <div className="p-2 bg-primary rounded-lg">
                        <Code2 className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Entry Point File</p>
                        <code className="text-lg font-mono font-bold text-primary">
                          {demoResults.entryPoint.file}
                        </code>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-4 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-primary" />
                        Execution Flow
                      </h4>
                      <div className="space-y-3">
                        {demoResults.entryPoint.flow.map((step, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="flex items-start gap-3"
                          >
                            <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-primary to-orange-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                              {index + 1}
                            </div>
                            <p className="flex-1 pt-1 text-sm">{step}</p>
                          </motion.div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-3">Code Snippet</h4>
                      <pre className="p-4 bg-muted/50 rounded-lg border border-border/50 overflow-x-auto">
                        <code className="text-sm font-mono">{demoResults.entryPoint.codeSnippet}</code>
                      </pre>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>

            {/* M3: Dependency Mapping */}
            <TabsContent value="m3" className="space-y-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Card className="border-primary/20 shadow-xl shadow-primary/5">
                  <CardHeader>
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-gradient-to-br from-primary to-orange-500 rounded-xl">
                        <GitBranch className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-2xl">Dependency Mapping</CardTitle>
                        <CardDescription>
                          How modules and files interact throughout the codebase
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="space-y-4">
                      {demoResults.dependencyMapping.graph.map((node, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.1 }}
                          className="relative"
                          style={{ marginLeft: `${(node.level - 1) * 40}px` }}
                        >
                          <div className="flex items-start gap-3 p-4 bg-muted/30 rounded-lg border border-border/50 hover:bg-muted/50 transition-colors">
                            <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${
                              node.level === 1
                                ? 'bg-gradient-to-br from-orange-500 to-red-500'
                                : node.level === 2
                                ? 'bg-gradient-to-br from-primary to-orange-500'
                                : node.level === 3
                                ? 'bg-gradient-to-br from-orange-400 to-yellow-500'
                                : 'bg-gradient-to-br from-yellow-400 to-orange-300'
                            }`}>
                              <Code2 className="w-5 h-5 text-white" />
                            </div>
                            <div className="flex-1">
                              <code className="text-sm font-mono font-semibold text-primary">
                                {node.file}
                              </code>
                              {node.imports.length > 0 && (
                                <div className="mt-2 flex flex-wrap gap-2">
                                  {node.imports.map((imp, impIndex) => (
                                    <Badge key={impIndex} variant="secondary" className="text-xs">
                                      → {imp}
                                    </Badge>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                          {index < demoResults.dependencyMapping.graph.length - 1 && (
                            <div className="ml-5 w-0.5 h-4 bg-gradient-to-b from-primary/50 to-transparent" />
                          )}
                        </motion.div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>

            {/* B1: Critical Files */}
            <TabsContent value="b1" className="space-y-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Card className="border-primary/20 shadow-xl shadow-primary/5">
                  <CardHeader>
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-gradient-to-br from-primary to-orange-500 rounded-xl">
                        <Star className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-2xl">Critical File Identification</CardTitle>
                        <CardDescription>
                          Files that play major roles in project execution
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {demoResults.criticalFiles.files.map((file, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="p-5 bg-gradient-to-r from-muted/30 to-accent/20 rounded-xl border border-border/50 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <code className="text-sm font-mono font-bold text-primary">
                              {file.name}
                            </code>
                            <p className="text-sm font-medium text-muted-foreground mt-1">
                              {file.role}
                            </p>
                          </div>
                          <Badge
                            variant={file.importance === 'critical' ? 'destructive' : 'default'}
                            className={file.importance === 'critical' ? 'bg-primary' : ''}
                          >
                            {file.importance}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">{file.description}</p>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Code2 className="w-3 h-3" />
                          <span>{file.linesOfCode} lines of code</span>
                        </div>
                      </motion.div>
                    ))}
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>

            {/* B2: Execution Flow */}
            <TabsContent value="b2" className="space-y-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Card className="border-primary/20 shadow-xl shadow-primary/5">
                  <CardHeader>
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-gradient-to-br from-primary to-orange-500 rounded-xl">
                        <TrendingUp className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-2xl">Execution Flow Explanation</CardTitle>
                        <CardDescription>
                          Runtime request flow for major operations
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {demoResults.executionFlow.scenarios.map((scenario, scenarioIndex) => (
                      <div key={scenarioIndex}>
                        <h4 className="font-semibold text-lg mb-4 flex items-center gap-2">
                          <Zap className="w-5 h-5 text-primary" />
                          {scenario.name}
                        </h4>
                        <div className="relative space-y-4">
                          {scenario.steps.map((step, index) => (
                            <motion.div
                              key={index}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.05 }}
                              className="relative flex gap-4"
                            >
                              <div className="flex flex-col items-center">
                                <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-primary to-orange-500 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg">
                                  {step.step}
                                </div>
                                {index < scenario.steps.length - 1 && (
                                  <div className="w-0.5 flex-1 bg-gradient-to-b from-primary/50 to-transparent min-h-8" />
                                )}
                              </div>
                              <div className="flex-1 pb-4">
                                <div className="p-4 bg-muted/30 rounded-lg border border-border/50">
                                  <p className="font-semibold text-sm mb-1">{step.component}</p>
                                  <code className="text-xs font-mono text-primary">{step.action}</code>
                                  <p className="text-sm text-muted-foreground mt-2">
                                    {step.description}
                                  </p>
                                </div>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>

            {/* B3: Repository Summary */}
            <TabsContent value="b3" className="space-y-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Card className="border-primary/20 shadow-xl shadow-primary/5">
                  <CardHeader>
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-gradient-to-br from-primary to-orange-500 rounded-xl">
                        <BookOpen className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-2xl">Intelligent Repository Summary</CardTitle>
                        <CardDescription>
                          High-level overview including tech stack and architecture
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="p-4 bg-gradient-to-r from-primary/10 to-orange-500/10 rounded-xl border border-primary/30">
                      <p className="text-lg">{demoResults.repositorySummary.overview}</p>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-4 flex items-center gap-2">
                        <Database className="w-5 h-5 text-primary" />
                        Tech Stack
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {demoResults.repositorySummary.techStack.map((tech, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: index * 0.05 }}
                            className="p-4 bg-muted/30 rounded-lg border border-border/50 hover:bg-muted/50 transition-colors"
                          >
                            <p className="font-semibold text-sm">{tech.name}</p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {tech.version} • {tech.category}
                            </p>
                          </motion.div>
                        ))}
                      </div>
                    </div>

                    <Separator />

                    <div>
                      <h4 className="font-semibold mb-3 flex items-center gap-2">
                        <Shield className="w-5 h-5 text-primary" />
                        Architecture: {demoResults.repositorySummary.architecture}
                      </h4>
                      <div className="space-y-2">
                        {demoResults.repositorySummary.patterns.map((pattern, index) => (
                          <div
                            key={index}
                            className="flex items-center gap-2 text-sm text-muted-foreground"
                          >
                            <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                            {pattern}
                          </div>
                        ))}
                      </div>
                    </div>

                    <Separator />

                    <div>
                      <h4 className="font-semibold mb-4">Key Design Decisions</h4>
                      <div className="space-y-3">
                        {demoResults.repositorySummary.keyDecisions.map((item, index) => (
                          <div key={index} className="p-4 bg-accent/20 rounded-lg border border-border/30">
                            <p className="font-semibold text-sm mb-2">{item.decision}</p>
                            <p className="text-sm text-muted-foreground">{item.rationale}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    <Separator />

                    <div>
                      <h4 className="font-semibold mb-4">Repository Metrics</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="p-4 bg-gradient-to-br from-primary/10 to-orange-500/10 rounded-xl border border-primary/20">
                          <p className="text-2xl font-bold text-primary">
                            {demoResults.repositorySummary.metrics.totalFiles}
                          </p>
                          <p className="text-sm text-muted-foreground mt-1">Total Files</p>
                        </div>
                        <div className="p-4 bg-gradient-to-br from-orange-500/10 to-yellow-500/10 rounded-xl border border-orange-500/20">
                          <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                            {demoResults.repositorySummary.metrics.linesOfCode.toLocaleString()}
                          </p>
                          <p className="text-sm text-muted-foreground mt-1">Lines of Code</p>
                        </div>
                        <div className="p-4 bg-gradient-to-br from-primary/10 to-orange-500/10 rounded-xl border border-primary/20">
                          <p className="text-2xl font-bold text-primary">
                            {demoResults.repositorySummary.metrics.testCoverage}%
                          </p>
                          <p className="text-sm text-muted-foreground mt-1">Test Coverage</p>
                          <Progress
                            value={demoResults.repositorySummary.metrics.testCoverage}
                            className="mt-2 h-2"
                          />
                        </div>
                        <div className="p-4 bg-gradient-to-br from-orange-400/10 to-yellow-400/10 rounded-xl border border-orange-400/20">
                          <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                            {demoResults.repositorySummary.metrics.dependencies}
                          </p>
                          <p className="text-sm text-muted-foreground mt-1">Dependencies</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>
    </div>
  );
}