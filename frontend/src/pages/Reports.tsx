import { useEffect, useState, useCallback } from 'react';
import { reportService, BACKEND_URL } from '../services/api';
import { Download, FileText, FileSpreadsheet, CheckCircle2, Trash2 } from 'lucide-react';
import { DataTable } from '../components/ui/DataTable';
import useStore from '../store';
import PageTransition from '../components/layout/PageTransition';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { ReportsAnalyticsCube } from '../components/3d/Internal3DElements';
import AWSOnboardingState from '../components/ui/AWSOnboardingState';
import AWSErrorState from '../components/ui/AWSErrorState';
import { SkeletonTable } from '../components/ui/Skeleton';

export default function Reports() {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasAWSError, setHasAWSError] = useState(false);
  
  // Form states
  const [reportType, setReportType] = useState('cost_summary');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const { addToast, user } = useStore();

  const loadReports = useCallback(async () => {
    if (user && !user.is_demo_mode && !user.is_aws_connected) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setHasAWSError(false);
    try {
      const data = await reportService.getReports();
      setReports(data);
    } catch (error: any) {
      console.error("Failed to load reports:", error);
      if (error.message && (error.message.includes("AWS_ERROR") || error.message.includes("AWS") || error.message.includes("credentials") || error.message.includes("502"))) {
        setHasAWSError(true);
      }
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  const handleGeneratePDF = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);
    addToast('Compiling custom PDF report...', 'info');
    try {
      const report = await reportService.generateReport({
        report_type: reportType,
        format: 'pdf'
      });
      addToast('PDF report compiled successfully!', 'success');
      loadReports();
      
      // Auto-trigger download
      const downloadUrl = `/static/reports/${report.filename}`;
      window.open(downloadUrl, '_blank');
    } catch (err: any) {
      addToast(err.message || 'Failed to generate PDF report', 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateCSV = async () => {
    setIsExporting(true);
    addToast('Compiling CSV spreadsheet...', 'info');
    try {
      const report = await reportService.generateReport({
        report_type: reportType,
        format: 'csv'
      });
      addToast('CSV export compiled successfully!', 'success');
      loadReports();

      // Auto-trigger download
      const downloadUrl = `/static/reports/${report.filename}`;
      window.open(downloadUrl, '_blank');
    } catch (err: any) {
      addToast(err.message || 'Failed to generate CSV export', 'error');
    } finally {
      setIsExporting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await reportService.deleteReport(id);
      addToast('Report deleted successfully', 'success');
      loadReports();
    } catch (err: any) {
      addToast(err.message || 'Failed to delete report', 'error');
    }
  };

  if (user && !user.is_demo_mode && !user.is_aws_connected) {
    return <AWSOnboardingState />;
  }

  if (hasAWSError) {
    return <AWSErrorState onRetry={loadReports} isLoading={loading} />;
  }

  return (
    <PageTransition>
      <div className="mb-8 relative">
        <div className="relative z-10">
          <h2 className="text-3xl font-bold tracking-tight mb-2">Reports & Exports</h2>
          <p className="text-text-secondary text-sm">Generate custom cost reports and schedule automated deliveries.</p>
        </div>
        <ReportsAnalyticsCube />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <Card>
            <CardHeader className="border-b border-border-primary pb-4 mb-6">
              <CardTitle className="flex items-center gap-2"><FileText size={18} /> Generate Custom Report</CardTitle>
            </CardHeader>
            
            <CardContent>
              <form onSubmit={handleGeneratePDF} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-text-primary">Report Type</label>
                    <select 
                      className="flex h-10 w-full rounded-lg border border-border-primary bg-background-primary px-3 py-2 text-sm text-text-primary focus-visible:outline-none focus-visible:border-accent-primary focus-visible:ring-2 focus-visible:ring-accent-primary/20 disabled:cursor-not-allowed disabled:opacity-55 transition-all duration-200 shadow-sm" 
                      value={reportType}
                      onChange={(e) => setReportType(e.target.value)}
                    >
                      <option value="cost_summary">Executive Summary</option>
                      <option value="detailed_breakdown">Detailed Cost Breakdown</option>
                      <option value="anomaly_report">Anomaly & Savings Report</option>
                      <option value="budget_variance">Budget Variance Report</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-text-primary">Date Range</label>
                    <select className="flex h-10 w-full rounded-lg border border-border-primary bg-background-primary px-3 py-2 text-sm text-text-primary focus-visible:outline-none focus-visible:border-accent-primary focus-visible:ring-2 focus-visible:ring-accent-primary/20 disabled:cursor-not-allowed disabled:opacity-55 transition-all duration-200 shadow-sm" defaultValue="Last 30 Days">
                      <option>Last 30 Days</option>
                      <option>Month to Date</option>
                      <option>Last Month</option>
                      <option>Year to Date</option>
                    </select>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-primary">Services to Include</label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    {['All Services', 'EC2', 'RDS', 'S3', 'Lambda', 'CloudFront'].map(svc => (
                      <label key={svc} className="flex items-center gap-3 text-sm text-text-secondary cursor-pointer hover:text-text-primary transition-colors select-none">
                        <input 
                          type="checkbox" 
                          defaultChecked={svc === 'All Services' || svc === 'EC2' || svc === 'RDS'} 
                        /> 
                        <span>{svc}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="pt-4 border-t border-border-primary flex flex-col sm:flex-row gap-4">
                  <Button type="submit" disabled={isGenerating} className="flex-1">
                    {isGenerating ? (
                      <><div className="w-4 h-4 border-2 border-[#FAFAFA]/30 border-t-[#FAFAFA] rounded-full animate-spin mr-2"></div> Generating PDF...</>
                    ) : (
                      <><Download size={16} className="mr-2" /> Generate PDF Report</>
                    )}
                  </Button>
                  <Button type="button" variant="secondary" onClick={handleGenerateCSV} disabled={isExporting} className="flex-1">
                    {isExporting ? "Generating..." : <><FileSpreadsheet size={16} className="mr-2" /> Export to CSV</>}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
        
        <div className="space-y-6">
          <Card>
            <CardHeader className="border-b border-border-primary pb-4 mb-6">
              <CardTitle className="flex items-center gap-2"><CheckCircle2 size={18} /> Generated Reports Log</CardTitle>
            </CardHeader>
            
            <CardContent>
              {loading ? (
                <SkeletonTable rows={3} cols={3} />
              ) : (
                <DataTable 
                  columns={[
                    { 
                      header: 'Report Name', 
                      accessorKey: 'filename', 
                      cell: ({ row }) => (
                        <span className="font-semibold text-text-primary font-mono text-xs">
                          {row.original.filename}
                        </span>
                      ) 
                    },
                    { 
                      header: 'Report Type', 
                      accessorKey: 'report_type', 
                      cell: ({ row }) => (
                        <span className="font-medium text-text-secondary text-sm capitalize">
                          {row.original.report_type.replace('_', ' ')}
                        </span>
                      ) 
                    },
                    { 
                      header: 'Action', 
                      id: 'action',
                      cell: ({ row }) => (
                        <div className="flex gap-2">
                          <a 
                            href={`/static/reports/${row.original.filename}`} 
                            target="_blank" 
                            rel="noreferrer"
                            className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-border-primary bg-background-primary hover:bg-background-elevated h-8 px-3 py-1 text-xs text-text-primary hover:text-accent-primary"
                          >
                            Download
                          </a>
                          <button 
                            onClick={() => handleDelete(row.original.id)}
                            className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-background-elevated h-8 px-2 py-1 text-xs text-danger hover:bg-danger/10"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      )
                    }
                  ]}
                  data={reports}
                />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </PageTransition>
  );
}
