import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { useNavigate } from 'react-router';
import {
  ArrowLeft, FolderTree, Zap, GitBranch, Star, TrendingUp, BookOpen, Code2, Shield, Box, Target, Download
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { ThemeToggle } from '../components/ThemeToggle';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Separator } from '../components/ui/separator';
import { useAnalysis } from '../context/AnalysisContext';
import { DependencyGraph } from '../components/DependencyGraph';

export function Results() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('b3'); // start on the summary tab initially since it's the highlight B3!
  const { analysisData } = useAnalysis();

  useEffect(() => {
    // If user refreshes on the results page manually and drops context, redirect home.
    if (!analysisData) {
      navigate('/');
    }
  }, [analysisData, navigate]);

  if (!analysisData) return null; // Avoid render errors until redirect happens

  const { repository, b3, m1, m2, m3, pdf_base64 } = analysisData;
  const repoName = repository.url.split('/').pop() || 'Repository';

  const downloadPdf = () => {
    if (!pdf_base64) return;
    const link = document.createElement('a');
    link.href = `data:application/pdf;base64,${pdf_base64}`;
    link.download = `${repoName}_analysis.pdf`;
    link.click();
  };

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
              <div className="p-2 bg-gradient-to-br from-primary to-orange-500 rounded-lg shadow-lg">
                <Code2 className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="font-semibold text-lg max-w-sm truncate">{repository.url}</h2>
                <p className="text-sm text-muted-foreground">{m1.total_folders} Folders • {repository.total_files} Files</p>
              </div>
            </div>
          </div>
          <div className="flex gap-4 items-center">
            {pdf_base64 && (
              <Button onClick={downloadPdf} className="flex gap-2 items-center bg-gradient-to-r from-orange-500 to-primary hover:opacity-90 transition-opacity">
                <Download className="w-4 h-4" />
                Download PDF Report
              </Button>
            )}
            <ThemeToggle />
          </div>
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
            <TabsList className="grid w-full grid-cols-2 md:grid-cols-6 h-auto p-1 bg-muted/30 backdrop-blur-sm gap-2">
              <TabsTrigger value="b3" className="flex flex-col items-center gap-2 py-3 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-orange-500 data-[state=active]:text-white data-[state=active]:shadow-xl">
                <BookOpen className="w-5 h-5" />
                <span className="text-xs font-medium">Summary</span>
              </TabsTrigger>
              <TabsTrigger value="m1" className="flex flex-col items-center gap-2 py-3 data-[state=active]:bg-primary data-[state=active]:text-white">
                <FolderTree className="w-5 h-5" />
                <span className="text-xs font-medium">Folder Structure</span>
              </TabsTrigger>
              <TabsTrigger value="m2" className="flex flex-col items-center gap-2 py-3 data-[state=active]:bg-primary data-[state=active]:text-white">
                <Zap className="w-5 h-5" />
                <span className="text-xs font-medium">Entry-Point & Flow</span>
              </TabsTrigger>
              <TabsTrigger value="m3" className="flex flex-col items-center gap-2 py-3 data-[state=active]:bg-primary data-[state=active]:text-white">
                <GitBranch className="w-5 h-5" />
                <span className="text-xs font-medium">Dependency Mapping</span>
              </TabsTrigger>
              <TabsTrigger value="b1" className="flex flex-col items-center gap-2 py-3 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-orange-500 data-[state=active]:text-white">
                <Star className="w-5 h-5" />
                <span className="text-xs font-medium">Critical files</span>
              </TabsTrigger>
              <TabsTrigger value="b2" className="flex flex-col items-center gap-2 py-3 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-orange-500 data-[state=active]:text-white">
                <TrendingUp className="w-5 h-5" />
                <span className="text-xs font-medium">Startup Mechanics</span>
              </TabsTrigger>
            </TabsList>

            {/* B3: Executive Repo Summary */}
            <TabsContent value="b3" className="space-y-4">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <Card className="border-primary/30 shadow-2xl shadow-primary/10 bg-card">
                  <CardHeader>
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-gradient-to-br from-primary to-orange-500 rounded-xl">
                        <BookOpen className="w-6 h-6 text-white" />
                      </div>
                      <div className="flex-1">
                        <CardTitle className="text-2xl">Executive Summary</CardTitle>
                        <CardDescription>Synthesized repository Intelligence combining structure, flow, and maps</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="p-6 bg-gradient-to-br from-primary/10 via-background to-orange-500/5 rounded-xl border border-primary/20 leading-relaxed text-lg tracking-wide rounded-t-xl rounded-b-md">
                      {b3.summary}
                    </div>

                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
                      <div className="p-4 bg-muted/20 border border-border/50 rounded-xl flex items-center gap-4">
                        <div className="bg-orange-500/20 p-2 rounded-lg text-orange-500"><Code2 /></div>
                        <div><p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Source Language</p><p className="font-semibold text-lg">{repository.language.toUpperCase()}</p></div>
                      </div>
                      <div className="p-4 bg-muted/20 border border-border/50 rounded-xl flex items-center gap-4">
                        <div className="bg-primary/20 p-2 rounded-lg text-primary"><Box /></div>
                        <div><p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Total Modules</p><p className="font-semibold text-lg">{m1.total_folders}</p></div>
                      </div>
                      <div className="p-4 bg-muted/20 border border-border/50 rounded-xl flex items-center gap-4">
                        <div className="bg-blue-500/20 p-2 rounded-lg text-blue-500"><GitBranch /></div>
                        <div><p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Total Files</p><p className="font-semibold text-lg">{repository.total_files}</p></div>
                      </div>
                      <div className="p-4 bg-muted/20 border border-border/50 rounded-xl flex items-center gap-4">
                        <div className="bg-green-500/20 p-2 rounded-lg text-green-500"><Target /></div>
                        <div><p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">M2 Entry Conf.</p><p className="font-semibold text-lg">{m2.confidence || "High"}</p></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>

            {/* M1: Folder Structure */}
            <TabsContent value="m1" className="space-y-4">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <Card className="border-border/50">
                  <CardHeader>
                    <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                      <div className="flex items-start gap-4">
                        <div className="p-3 bg-primary rounded-xl"><FolderTree className="w-6 h-6 text-white" /></div>
                        <div>
                          <CardTitle className="text-2xl">Module Analysis</CardTitle>
                          <CardDescription>Intelligent folder explanations via pattern matching & AI</CardDescription>
                        </div>
                      </div>
                      <Badge variant="outline" className="text-primary border-primary">{m1.architecture_hint}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {m1.folder_tree ? Object.entries(m1.folder_tree).map(([folderName, data]: [string, any], i) => (
                      <motion.div key={folderName} initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: i * 0.05 }}>
                        <div className="p-5 border border-border/50 bg-card rounded-xl shadow-sm space-y-3">
                          <div className="flex justify-between items-start">
                            <div className="flex gap-3">
                              <Box className="w-5 h-5 text-primary" />
                              <div>
                                <code className="text-base font-bold text-foreground bg-muted px-2 py-0.5 rounded">{folderName}</code>
                                <p className="text-secondary-foreground font-medium mt-2">{data.description}</p>
                              </div>
                            </div>
                            <Badge className={data.source === 'llm_fallback' ? 'bg-orange-600' : 'bg-green-600'}>
                              {data.source === 'llm_fallback' ? '🤖 AI Inferred' : '⚡ Pattern Match'}
                            </Badge>
                          </div>
                          <div className="ml-8 mt-4 pt-3 border-t border-border/40 grid grid-cols-2 md:grid-cols-4 gap-2">
                            {data.files?.slice(0, 10).map((f: string) => (
                              <div key={f} className="text-xs text-muted-foreground truncate" title={f}>📄 {f.split('/').pop()}</div>
                            ))}
                            {data.files?.length > 10 && <div className="text-xs text-muted-foreground">...and {data.files.length - 10} more</div>}
                          </div>
                        </div>
                      </motion.div>
                    )) : <p>No folder data available</p>}
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>

            {/* M2: Entry Point */}
            <TabsContent value="m2" className="space-y-4">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <Card className="border-border/50">
                  <CardHeader>
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-primary rounded-xl"><Zap className="w-6 h-6 text-white" /></div>
                      <div>
                        <CardTitle className="text-2xl">Entry Point Detection</CardTitle>
                        <CardDescription>Primary execution file and graph-derived boundaries</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="p-5 bg-gradient-to-br from-primary/10 to-transparent border border-primary/20 rounded-xl">
                      <p className="text-sm font-semibold tracking-wider text-primary uppercase mb-2 flex items-center gap-2"><Target className="w-4 h-4" /> Detected Entry Point</p>
                      <code className="text-2xl font-black bg-primary/10 text-primary px-3 py-1 rounded-md">{m2.entry_file}</code>
                    </div>

                    {m2.first_level_deps && m2.first_level_deps.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-lg mb-3">Core First-Level Dependencies</h4>
                        <div className="flex flex-wrap gap-2">
                          {m2.first_level_deps.map((dep: string) => (
                            <Badge key={dep} variant="secondary" className="px-3 py-1.5 font-mono bg-muted/50 border border-border">
                              {dep}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>

            {/* M3: React Flow Dependencies Canvas */}
            <TabsContent value="m3" className="space-y-4">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <Card className="border-border/50 overflow-hidden">
                  <CardHeader className="bg-muted/10 border-b border-border/40 pb-4">
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-primary rounded-xl"><GitBranch className="w-6 h-6 text-white" /></div>
                      <div>
                        <CardTitle className="text-2xl">Codebase Map Canvas</CardTitle>
                        <CardDescription>Interactive dependency graph algorithmically auto-placed</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="p-0">
                    {/* Injecting Our React Flow Canvas Here */}
                    {m3.react_flow_data ? (
                      <DependencyGraph reactFlowData={m3.react_flow_data} />
                    ) : (
                      <div className="p-12 text-center text-muted-foreground">Unable to render React Flow canvas.</div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>

            {/* B1: Critical Files */}
            <TabsContent value="b1" className="space-y-4">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <Card className="border-border/50">
                  <CardHeader>
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl">
                        <Star className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-2xl">Critical Infrastructure</CardTitle>
                        <CardDescription>Files forming the backbone of the architecture</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4">
                      {m3.graph_stats?.critical_files?.length > 0 ? m3.graph_stats.critical_files.map((file: string, index: number) => (
                        <div key={file} className="flex justify-between items-center p-4 border border-border/50 rounded-xl bg-card hover:border-orange-500/50 transition-colors group">
                          <code className="text-lg font-mono font-medium">{file}</code>
                          <Badge className="bg-orange-500 hover:bg-orange-500/80">Critical Path Node</Badge>
                        </div>
                      )) : <p className="text-muted-foreground">No overwhelmingly critical hub files detected.</p>}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>

            {/* Exec Flow (Gemini Analysis) */}
            <TabsContent value="b2" className="space-y-4">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <Card className="border-border/50">
                  <CardHeader>
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-gradient-to-br from-primary to-blue-500 rounded-xl">
                        <TrendingUp className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-2xl">Intelligent Execution Mechanics</CardTitle>
                        <CardDescription>AI-generated breakdown of the app lifecycle</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="p-6 rounded-xl bg-muted/20 border border-border/50 whitespace-pre-wrap leading-relaxed text-lg shadow-inner">
                      {m2.explanation}
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