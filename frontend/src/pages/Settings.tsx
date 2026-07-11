import { useState, useEffect } from 'react';
import { Save, Key, User, Shield, Bell, Info, Activity } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import useStore from '../store';
import { settingsService, authService, auditService } from '../services/api';
import PageTransition from '../components/layout/PageTransition';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { SettingsHoloSphere } from '../components/3d/Internal3DElements';
import { SkeletonTable } from '../components/ui/Skeleton';

export default function Settings() {
  const { theme, toggleTheme, user, setUser, addToast } = useStore();
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get('tab');
  const [activeTab, setActiveTab] = useState(tabParam || 'general');

  useEffect(() => {
    if (tabParam) {
      setActiveTab(tabParam);
    }
  }, [tabParam]);

  const [settings, setSettings] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Audit Logs states
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loadingAudit, setLoadingAudit] = useState(false);

  // General tab states
  const [fullName, setFullName] = useState('');
  const [emailAddress, setEmailAddress] = useState('');
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  // AWS tab states
  const [awsAccountId, setAwsAccountId] = useState('');
  const [awsRoleArn, setAwsRoleArn] = useState('');
  const [isConnectingAWS, setIsConnectingAWS] = useState(false);

  // Security tab states
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await settingsService.getSettings();
        setSettings(data);
      } catch (err) {
        console.error('Failed to fetch settings:', err);
      }
    };
    fetchSettings();
  }, []);

  useEffect(() => {
    if (activeTab === 'audit') {
      const fetchAudits = async () => {
        setLoadingAudit(true);
        try {
          const data = await auditService.getAuditLogs(1, 20);
          setAuditLogs(data.items || []);
        } catch (err) {
          console.error('Failed to fetch audit logs:', err);
        } finally {
          setLoadingAudit(false);
        }
      };
      fetchAudits();
    }
  }, [activeTab]);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setEmailAddress(user.email || '');
    }
  }, [user]);

  const handleSaveSettings = async (updatedSettings = settings) => {
    if (!updatedSettings) return;
    setIsSaving(true);
    try {
      const data = await settingsService.updateSettings(updatedSettings);
      setSettings(data);
      addToast('Preferences saved successfully', 'success');
    } catch (err: any) {
      addToast(err.message || 'Failed to save settings', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    const fetchAWS = async () => {
      try {
        const data = await settingsService.getAWSAccount();
        setAwsAccountId(data.account_id || '');
        setAwsRoleArn(data.role_arn || '');
      } catch (err) {
        console.error('Failed to fetch AWS settings:', err);
      }
    };
    fetchAWS();
  }, []);

  const handleConnectAWS = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!awsAccountId.trim() || !awsRoleArn.trim()) {
      addToast('AWS Account ID and Role ARN are required', 'warning');
      return;
    }
    setIsConnectingAWS(true);
    try {
      await settingsService.updateAWSAccount({
        account_id: awsAccountId,
        role_arn: awsRoleArn
      });
      addToast('AWS Account connected successfully', 'success');
    } catch (err: any) {
      addToast(err.message || 'Failed to connect AWS Account', 'error');
    } finally {
      setIsConnectingAWS(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim() || !emailAddress.trim()) {
      addToast('Name and email are required', 'warning');
      return;
    }
    setIsSavingProfile(true);
    try {
      const updatedUser = await authService.updateProfile({
        full_name: fullName,
        email: emailAddress
      });
      setUser(updatedUser);
      addToast('Profile updated successfully', 'success');
    } catch (err: any) {
      addToast(err.message || 'Failed to update profile', 'error');
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword) {
      addToast('Current password is required', 'warning');
      return;
    }
    if (newPassword.length < 8) {
      addToast('New password must be at least 8 characters', 'warning');
      return;
    }
    if (newPassword !== confirmPassword) {
      addToast('New passwords do not match', 'warning');
      return;
    }
    setIsUpdatingPassword(true);
    try {
      await authService.changePassword({
        current_password: currentPassword,
        new_password: newPassword
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      addToast('Password updated successfully', 'success');
    } catch (err: any) {
      addToast(err.message || 'Failed to update password', 'error');
    } finally {
      setIsUpdatingPassword(false);
    }
  };

  const handleToggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    toggleTheme();
    if (settings) {
      const nextSettings = { ...settings, theme: nextTheme };
      setSettings(nextSettings);
      handleSaveSettings(nextSettings);
    }
  };

  const tabs = [
    { id: 'general', label: 'General', icon: User },
    { id: 'aws', label: 'AWS Integration', icon: Key },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'audit', label: 'Audit Trail', icon: Activity },
  ];

  return (
    <PageTransition>
      <div className="mb-8 relative">
        <div className="relative z-10">
          <h2 className="text-3xl font-bold tracking-tight mb-2">Settings</h2>
          <p className="text-text-secondary text-sm">Manage your account, preferences, and integrations.</p>
        </div>
        <SettingsHoloSphere />
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        <div className="w-full md:w-64 shrink-0">
          <nav className="flex flex-col gap-1">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  setSearchParams({ tab: tab.id });
                }}
                className={`relative flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${
                  activeTab === tab.id 
                    ? 'bg-accent-primary/8 text-accent-primary border-accent-primary/15 shadow-sm' 
                    : 'text-text-secondary border-transparent hover:bg-background-secondary/60 hover:text-text-primary'
                }`}
              >
                {activeTab === tab.id && (
                  <span className="absolute left-0 top-3 bottom-3 w-1 rounded-r-md bg-accent-primary" />
                )}
                <tab.icon size={18} className={activeTab === tab.id ? 'text-accent-primary' : 'text-text-muted'} />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex-1 max-w-3xl">
          {activeTab === 'general' && (
            <Card className="animate-fade-in">
              <CardHeader className="border-b border-border-primary pb-4 mb-6">
                <CardTitle>General Settings</CardTitle>
              </CardHeader>
              
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-sm text-text-primary">Theme Preference</h4>
                    <p className="text-sm text-text-secondary mt-1">Choose between light and dark mode for the dashboard.</p>
                  </div>
                  <button 
                    onClick={handleToggleTheme}
                    className="relative w-14 h-8 rounded-full bg-background-elevated border border-border-primary flex items-center px-1 transition-colors"
                  >
                    <div className={`w-6 h-6 rounded-full bg-accent-primary shadow-md transform transition-transform ${theme === 'dark' ? 'translate-x-6' : 'translate-x-0'}`}></div>
                  </button>
                </div>
                
                <hr className="border-border-primary" />
                
                <form onSubmit={handleSaveProfile} className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-text-primary">Full Name</label>
                    <Input 
                      type="text" 
                      className="max-w-md" 
                      value={fullName} 
                      onChange={(e) => setFullName(e.target.value)}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-text-primary">Email Address</label>
                    <Input 
                      type="email" 
                      className="max-w-md" 
                      value={emailAddress}
                      onChange={(e) => setEmailAddress(e.target.value)}
                    />
                  </div>
                  
                  <div className="pt-4">
                    <Button type="submit" disabled={isSavingProfile}>
                      {isSavingProfile ? "Saving..." : <><Save size={16} /> Save Changes</>}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          {activeTab === 'aws' && (
            <Card className="animate-fade-in">
              <CardHeader className="border-b border-border-primary pb-4 mb-6">
                <CardTitle>AWS Integration</CardTitle>
              </CardHeader>
              
              <CardContent>
                <div className="bg-accent-cyan/10 border border-accent-cyan/20 text-accent-cyan px-4 py-3 rounded-lg text-sm mb-6 flex gap-3">
                  <Info size={20} className="shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium mb-1">IAM Role Setup Required</p>
                    <p className="opacity-90">To analyze your costs, CloudWise needs read-only access to Cost Explorer and your billing bucket.</p>
                  </div>
                </div>
                
                <form onSubmit={handleConnectAWS} className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-text-primary">AWS Account ID</label>
                    <Input 
                      type="text" 
                      className="max-w-md font-mono" 
                      placeholder="123456789012" 
                      value={awsAccountId}
                      onChange={(e) => setAwsAccountId(e.target.value)}
                      required
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-text-primary">Cross-Account Role ARN</label>
                    <Input 
                      type="text" 
                      className="w-full font-mono text-sm" 
                      placeholder="arn:aws:iam::123456789012:role/CloudWiseReadOnlyRole" 
                      value={awsRoleArn}
                      onChange={(e) => setAwsRoleArn(e.target.value)}
                      required
                    />
                    <p className="text-xs text-text-muted mt-2">Use the CloudFormation template to create this role automatically.</p>
                  </div>
                  
                  <div className="pt-4 flex gap-3">
                    <Button type="submit" disabled={isConnectingAWS}>
                      <Key size={16} /> {isConnectingAWS ? "Connecting..." : "Connect Account"}
                    </Button>
                    <Button type="button" variant="secondary" onClick={() => addToast('CloudFormation Template download started', 'success')}>
                      Download Template
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}
          
          {activeTab === 'security' && (
            <Card className="animate-fade-in">
              <CardHeader className="border-b border-border-primary pb-4 mb-6">
                <CardTitle>Security & Authentication</CardTitle>
              </CardHeader>
              
              <CardContent className="space-y-6">
                <div>
                  <h4 className="font-medium text-text-primary mb-4">Change Password</h4>
                  <form onSubmit={handleUpdatePassword} className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-text-primary">Current Password</label>
                      <Input 
                        type="password" 
                        className="max-w-md" 
                        autoComplete="current-password"
                        placeholder="••••••••" 
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-text-primary">New Password</label>
                      <Input 
                        type="password" 
                        className="max-w-md" 
                        autoComplete="new-password"
                        placeholder="••••••••" 
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-text-primary">Confirm New Password</label>
                      <Input 
                        type="password" 
                        className="max-w-md" 
                        autoComplete="new-password"
                        placeholder="••••••••" 
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                      />
                    </div>
                    <Button type="submit" variant="secondary" disabled={isUpdatingPassword}>
                      {isUpdatingPassword ? "Updating..." : "Update Password"}
                    </Button>
                  </form>
                </div>
                
                <hr className="border-border-primary" />
                
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-text-primary">Two-Factor Authentication (2FA)</h4>
                    <p className="text-sm text-text-secondary mt-1">Add an extra layer of security to your account.</p>
                  </div>
                  <Button 
                    onClick={() => {
                      const next2FA = !settings?.two_factor_enabled;
                      const nextSettings = { ...settings, two_factor_enabled: next2FA };
                      setSettings(nextSettings);
                      handleSaveSettings(nextSettings);
                    }} 
                  >
                    {settings?.two_factor_enabled ? "Disable 2FA" : "Enable 2FA"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'notifications' && (
            <Card className="animate-fade-in">
              <CardHeader className="border-b border-border-primary pb-4 mb-6">
                <CardTitle>Alerts & Notifications</CardTitle>
              </CardHeader>
              
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between p-4 border border-border-primary rounded-lg bg-background-elevated">
                  <div>
                    <h4 className="font-medium text-text-primary text-sm mb-1">Budget Alerts</h4>
                    <p className="text-xs text-text-secondary">Receive notifications when budgets cross threshold limits.</p>
                  </div>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2.5 text-sm text-text-secondary hover:text-text-primary cursor-pointer transition-colors select-none">
                      <input 
                        type="checkbox" 
                        checked={settings?.email_alerts || false} 
                        onChange={(e) => {
                          const nextSettings = {...settings, email_alerts: e.target.checked};
                          setSettings(nextSettings);
                          handleSaveSettings(nextSettings);
                        }} 
                      /> 
                      <span>Email</span>
                    </label>
                    <label className="flex items-center gap-2.5 text-sm text-text-secondary hover:text-text-primary cursor-pointer transition-colors select-none">
                      <input 
                        type="checkbox" 
                        checked={settings?.slack_alerts || false} 
                        onChange={(e) => {
                          const nextSettings = {...settings, slack_alerts: e.target.checked};
                          setSettings(nextSettings);
                          handleSaveSettings(nextSettings);
                        }} 
                      /> 
                      <span>Slack</span>
                    </label>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 border border-border-primary rounded-lg bg-background-elevated">
                  <div>
                    <h4 className="font-medium text-text-primary text-sm mb-1">Weekly Cost Summary</h4>
                    <p className="text-xs text-text-secondary">A digest of your weekly spending, forecasts, and AI insights.</p>
                  </div>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2.5 text-sm text-text-secondary hover:text-text-primary cursor-pointer transition-colors select-none">
                      <input 
                        type="checkbox" 
                        checked={settings?.weekly_reports || false} 
                        onChange={(e) => {
                          const nextSettings = {...settings, weekly_reports: e.target.checked};
                          setSettings(nextSettings);
                          handleSaveSettings(nextSettings);
                        }} 
                      /> 
                      <span>Email</span>
                    </label>
                  </div>
                </div>

                <div className="space-y-2 pt-4 border-t border-border-primary">
                  <label className="text-sm font-medium text-text-primary">Slack Webhook URL</label>
                  <Input 
                    type="url" 
                    value={settings?.slack_webhook_url || ''} 
                    onChange={(e) => setSettings({...settings, slack_webhook_url: e.target.value})} 
                    className="w-full font-mono text-sm" 
                    placeholder="https://hooks.slack.com/services/..." 
                  />
                </div>

                <div className="pt-2">
                  <Button onClick={() => handleSaveSettings(settings)} disabled={isSaving}>
                    {isSaving ? "Saving..." : "Save Notification Preferences"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'audit' && (
            <Card className="animate-fade-in">
              <CardHeader className="border-b border-border-primary pb-4 mb-6">
                <CardTitle className="flex items-center gap-2">
                  <Activity size={18} /> Governance & Audit Trail
                </CardTitle>
              </CardHeader>
              
              <CardContent>
                {loadingAudit ? (
                  <SkeletonTable rows={4} cols={5} />
                ) : (
                  <div className="rounded-xl border border-border-primary bg-background-secondary overflow-hidden shadow-sm">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-background-elevated border-b border-border-primary text-[10px] font-bold uppercase tracking-wider text-text-muted">
                        <tr>
                          <th className="py-3 px-4">Timestamp</th>
                          <th className="py-3 px-4">Action</th>
                          <th className="py-3 px-4">Resource</th>
                          <th className="py-3 px-4">Description</th>
                          <th className="py-3 px-4">IP Address</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-primary/50 bg-background-secondary/20">
                        {auditLogs.map((log: any) => (
                          <tr key={log.id} className="text-text-primary hover:bg-background-elevated/60 transition-colors">
                            <td className="py-3.5 px-4 text-xs font-mono text-text-secondary">
                              {new Date(log.created_at).toLocaleString()}
                            </td>
                            <td className="py-3.5 px-4">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                log.action === 'login' ? 'bg-success/15 text-success border border-success/20' :
                                log.action === 'register' ? 'bg-accent-cyan/15 text-accent-cyan border border-accent-cyan/20' :
                                log.action === 'create' ? 'bg-accent-primary/15 text-accent-primary border border-accent-primary/20' :
                                log.action === 'delete' ? 'bg-danger/15 text-danger border border-danger/20' : 'bg-text-muted/15 text-text-muted border border-border-primary'
                              }`}>
                                {log.action}
                              </span>
                            </td>
                            <td className="py-3.5 px-4 text-xs font-mono text-text-secondary">
                              {log.resource_type || '-'}
                            </td>
                            <td className="py-3.5 px-4 font-medium">
                              {log.description || '-'}
                            </td>
                            <td className="py-3.5 px-4 text-xs font-mono text-text-secondary">
                              {log.ip_address || '-'}
                            </td>
                          </tr>
                        ))}
                        {auditLogs.length === 0 && (
                          <tr>
                            <td colSpan={5} className="py-8 text-center text-text-muted font-medium text-xs">
                              No logs recorded yet.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </PageTransition>
  );
}
