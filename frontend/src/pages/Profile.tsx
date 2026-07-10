import React, { useState, useEffect } from 'react';
import { Save, Key, Shield, User as UserIcon, RefreshCw, Mail, Activity, Cloud, Lock } from 'lucide-react';
import useStore from '../store';
import { authService, settingsService, auditService } from '../services/api';
import PageTransition from '../components/layout/PageTransition';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import Badge from '../components/ui/Badge';

export default function Profile() {
  const { user, setUser, addToast } = useStore();

  // Profile forms
  const [fullName, setFullName] = useState('');
  const [emailAddress, setEmailAddress] = useState('');
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  // Security forms
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false);

  // Stats / Metadata
  const [awsAccountId, setAwsAccountId] = useState('');
  const [lastActivity, setLastActivity] = useState<string>('Recent');
  const [isLoadingStats, setIsLoadingStats] = useState(true);

  // Simulated avatar gradient
  const [avatarColor] = useState(() => {
    const gradients = [
      'from-indigo-500 to-purple-600',
      'from-blue-500 to-indigo-600',
      'from-cyan-500 to-blue-600',
      'from-emerald-500 to-teal-600',
    ];
    return gradients[Math.floor(Math.random() * gradients.length)];
  });

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setEmailAddress(user.email || '');
    }
  }, [user]);

  useEffect(() => {
    const fetchMetadata = async () => {
      setIsLoadingStats(true);
      try {
        const [awsData, auditsData] = await Promise.all([
          settingsService.getAWSAccount().catch(() => ({ account_id: '' })),
          auditService.getAuditLogs(1, 5).catch(() => ({ items: [] }))
        ]);
        
        setAwsAccountId(awsData?.account_id || 'Not Connected');
        
        if (auditsData?.items && auditsData.items.length > 0) {
          const latest = new Date(auditsData.items[0].created_at);
          setLastActivity(latest.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ' ' + latest.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
        }
      } catch (err) {
        console.error('Failed to load profile metadata:', err);
      } finally {
        setIsLoadingStats(false);
      }
    };
    fetchMetadata();
  }, []);

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
      addToast('Profile information updated successfully', 'success');
    } catch (err: any) {
      addToast(err.message || 'Failed to update profile', 'error');
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword) {
      addToast('Current password is required to change password', 'warning');
      return;
    }
    if (newPassword.length < 8) {
      addToast('New password must be at least 8 characters long', 'warning');
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
      addToast('Password has been updated successfully', 'success');
    } catch (err: any) {
      addToast(err.message || 'Failed to update password', 'error');
    } finally {
      setIsUpdatingPassword(false);
    }
  };

  const initials = fullName
    ? fullName.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
    : 'U';

  return (
    <PageTransition>
      {/* SaaS Premium Header Card */}
      <div className="relative mb-8 rounded-2xl overflow-hidden border border-border-primary bg-background-elevated shadow-xl">
        <div className="h-32 bg-gradient-to-r from-blue-600/30 via-indigo-600/30 to-purple-600/30 absolute inset-0 z-0 animate-pulse" />
        <div className="relative z-10 p-6 md:p-8 pt-12 md:pt-16 flex flex-col md:flex-row items-center md:items-start justify-between gap-6">
          <div className="flex flex-col md:flex-row items-center gap-6 text-center md:text-left">
            <div className={`w-24 h-24 md:w-28 md:h-28 rounded-full bg-gradient-to-tr ${avatarColor} flex items-center justify-center text-[#FAFAFA] text-3xl font-bold shadow-2xl border-4 border-[var(--bg-elevated)] relative group`}>
              {initials}
              <div className="absolute inset-0 rounded-full bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-xs font-semibold cursor-pointer">
                Edit Avatar
              </div>
            </div>
            <div className="mt-2 md:mt-4">
              <div className="flex flex-col md:flex-row items-center gap-2 mb-1.5 justify-center md:justify-start">
                <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight text-text-primary">{fullName || 'User'}</h2>
                <Badge variant="healthy">Active</Badge>
              </div>
              <p className="text-text-secondary text-sm md:text-base font-medium flex items-center justify-center md:justify-start gap-1.5 mb-2">
                <Mail size={16} className="text-text-muted" /> {emailAddress}
              </p>
              <div className="flex flex-wrap gap-2 justify-center md:justify-start text-xs font-semibold text-text-muted">
                <span className="bg-background-primary px-2.5 py-1 rounded-full border border-border-primary capitalize">
                  Role: {user?.role || 'Member'}
                </span>
                <span className="bg-background-primary px-2.5 py-1 rounded-full border border-border-primary">
                  Enterprise Account
                </span>
              </div>
            </div>
          </div>
          <div className="flex flex-row md:flex-col gap-2 shrink-0 justify-center w-full md:w-auto md:self-end mt-4 md:mt-0">
            <Button variant="secondary" onClick={() => addToast('Avatar upload simulated successfully', 'success')} className="flex-1 md:flex-none">
              Upload Photo
            </Button>
          </div>
        </div>
      </div>

      {/* Profile Overview Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="bg-background-elevated hover:shadow-md transition-shadow">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center shrink-0">
              <UserIcon size={22} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs text-text-muted font-semibold uppercase tracking-wider">Account Role</div>
              <div className="text-lg font-bold text-text-primary capitalize truncate">{user?.role || 'Member'}</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-background-elevated hover:shadow-md transition-shadow">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-500 flex items-center justify-center shrink-0">
              <Activity size={22} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs text-text-muted font-semibold uppercase tracking-wider">Last Activity</div>
              <div className="text-sm font-bold text-text-primary truncate">{isLoadingStats ? 'Loading...' : lastActivity}</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-background-elevated hover:shadow-md transition-shadow">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-accent-cyan/10 text-accent-cyan flex items-center justify-center shrink-0">
              <Cloud size={22} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs text-text-muted font-semibold uppercase tracking-wider">AWS Account</div>
              <div className="text-sm font-bold text-text-primary font-mono truncate">{isLoadingStats ? 'Loading...' : awsAccountId}</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-background-elevated hover:shadow-md transition-shadow">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center shrink-0">
              <Shield size={22} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs text-text-muted font-semibold uppercase tracking-wider">2FA Status</div>
              <div className="text-lg font-bold text-text-primary truncate">Enabled</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Edit Sections Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Personal Details */}
        <Card className="shadow-lg">
          <CardHeader className="border-b border-border-primary pb-4 mb-6">
            <CardTitle className="flex items-center gap-2">
              <UserIcon size={18} className="text-accent-primary" /> Personal Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSaveProfile} className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-text-primary">Full Name</label>
                <Input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="John Doe"
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-text-primary">Email Address</label>
                <Input
                  type="email"
                  value={emailAddress}
                  onChange={(e) => setEmailAddress(e.target.value)}
                  placeholder="john.doe@company.com"
                  required
                />
              </div>

              <div className="pt-4 border-t border-border-primary flex justify-end">
                <Button type="submit" disabled={isSavingProfile} className="w-full sm:w-auto">
                  {isSavingProfile ? (
                    <><RefreshCw size={16} className="animate-spin mr-1" /> Saving...</>
                  ) : (
                    <><Save size={16} className="mr-1" /> Save Profile</>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Change Password */}
        <Card className="shadow-lg">
          <CardHeader className="border-b border-border-primary pb-4 mb-6">
            <CardTitle className="flex items-center gap-2">
              <Lock size={18} className="text-accent-primary" /> Password & Security
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleUpdatePassword} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-text-primary">Current Password</label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  autoComplete="current-password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-text-primary">New Password</label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  autoComplete="new-password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-text-primary">Confirm New Password</label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>

              <div className="pt-4 border-t border-border-primary flex justify-end">
                <Button type="submit" variant="secondary" disabled={isUpdatingPassword} className="w-full sm:w-auto">
                  {isUpdatingPassword ? (
                    <><RefreshCw size={16} className="animate-spin mr-1" /> Updating...</>
                  ) : (
                    <><Key size={16} className="mr-1" /> Update Password</>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  );
}
