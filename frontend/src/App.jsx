import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import FoodLogger from './components/FoodLogger';
import RiskAnalysis from './components/RiskAnalysis';
import Recommendations from './components/Recommendations';
import LogHistory from './components/LogHistory';
import UserProfile from './components/UserProfile';
import AuthModal from './components/AuthModal';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [userProfile, setUserProfile] = useState(null);
  const [dailyData, setDailyData] = useState(null);

  useEffect(() => {
    const savedUser = localStorage.getItem('nutri_user');
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser);
        setUserProfile(parsed);
        fetchProfile(parsed.id);
        fetchDailyLogs(parsed.id);
      } catch (e) {
        localStorage.removeItem('nutri_user');
      }
    } else {
      fetchProfile(1);
      fetchDailyLogs(1);
    }
  }, []);

  const fetchProfile = async (uid = 1) => {
    try {
      const res = await axios.get(`/api/auth/me/${uid}`);
      setUserProfile(res.data);
      localStorage.setItem('nutri_user', JSON.stringify(res.data));
    } catch (err) {
      console.error('Error loading profile:', err);
    }
  };

  const fetchDailyLogs = async (uid = 1) => {
    try {
      const currentId = userProfile?.id || uid;
      const res = await axios.get(`/api/logs/daily/${currentId}`);
      setDailyData(res.data);
    } catch (err) {
      console.error('Error loading daily logs:', err);
    }
  };

  const handleLoginSuccess = (user) => {
    setUserProfile(user);
    fetchDailyLogs(user.id);
  };

  const handleLogout = () => {
    localStorage.removeItem('nutri_token');
    localStorage.removeItem('nutri_user');
    setUserProfile(null);
  };

  if (!userProfile) {
    return <AuthModal onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="app-layout">
      
      {/* Sleek Left Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        userProfile={userProfile}
        onLogout={handleLogout}
      />

      {/* Main Expansive Content Area */}
      <main className="main-content">
        {activeTab === 'dashboard' && (
          <Dashboard dailyData={dailyData} onNavigate={(tab) => setActiveTab(tab)} />
        )}
        {activeTab === 'logger' && (
          <FoodLogger userProfile={userProfile} dailyData={dailyData} refreshData={() => fetchDailyLogs(userProfile.id)} />
        )}
        {activeTab === 'risk' && (
          <RiskAnalysis userProfile={userProfile} onNavigate={(tab) => setActiveTab(tab)} />
        )}
        {activeTab === 'recommendations' && (
          <Recommendations userProfile={userProfile} dailyData={dailyData} onNavigate={(tab) => setActiveTab(tab)} />
        )}
        {activeTab === 'history' && (
          <LogHistory userProfile={userProfile} />
        )}
        {activeTab === 'profile' && (
          <UserProfile userProfile={userProfile} onProfileUpdate={() => fetchProfile(userProfile.id)} />
        )}
      </main>

    </div>
  );
}
