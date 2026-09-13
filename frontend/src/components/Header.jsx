import React, { useState, useEffect, useRef } from 'react';
import styles from './Header.module.css';

const CustomSelect = ({ label, value, options, onChange, disabled }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={styles.selectWrapper} ref={dropdownRef}>
      <label className={styles.selectLabel}>{label}</label>
      <div 
        className={`${styles.glassSelectValue} ${disabled ? styles.disabled : ''} ${isOpen ? styles.active : ''}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        data-testid={`${label.toLowerCase()}-select`}
      >
        <span className={styles.selectedValueText}>{value || 'Select...'}</span>
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          width="14" 
          height="14" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          className={`${styles.chevron} ${isOpen ? styles.rotate : ''}`}
        >
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </div>
      
      {isOpen && !disabled && (
        <div className={styles.glassOptionsList}>
          {options.map(opt => (
            <div 
              key={opt} 
              className={`${styles.glassOption} ${opt === value ? styles.selected : ''}`}
              onClick={() => {
                onChange(opt);
                setIsOpen(false);
              }}
              data-value={opt}
            >
              {opt}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const NAV_TABS = [
  { id: 'briefing', label: 'Executive Briefing', icon: '📊' },
  { id: 'explorer', label: 'Corridor Map Explorer', icon: '🗺️' }
];

const Header = ({ 
  suburbs = [], 
  selectedSuburb, 
  selectedStreet, 
  onSuburbChange, 
  onStreetChange,
  activeTab,
  onTabChange,
  summaryMetrics
}) => {
  const currentSuburb = suburbs.find(s => s.name === selectedSuburb);
  const streets = currentSuburb ? ['All Streets', ...currentSuburb.streets] : [];

  return (
    <header className={styles.headerContainer} id="app-header">
      <div className={styles.topRow}>
        <div className={styles.brandSection}>
          <div className={styles.badgeGov}>State Government of Victoria</div>
          <div className={styles.brandTitleRow}>
            <h1 className={styles.mainTitle}>Urban Mobility & Kerbside Analytics</h1>
            <span className={styles.versionBadge}>v2.0 Executive</span>
          </div>
          <p className={styles.subtitle}>Empirical Assessment: Parking Use vs Protected Bike Lane Infrastructure</p>
        </div>

        <div className={styles.filterSection}>
          <CustomSelect 
            label="Suburb" 
            value={selectedSuburb} 
            options={suburbs.map(s => s.name)} 
            onChange={onSuburbChange} 
          />
          
          <CustomSelect 
            label="Street Corridor" 
            value={selectedStreet} 
            options={streets} 
            onChange={onStreetChange} 
            disabled={streets.length === 0}
          />
        </div>
      </div>

      <div className={styles.bottomRow}>
        <nav className={styles.navTabs}>
          {NAV_TABS.map(tab => (
            <button
              key={tab.id}
              className={`${styles.tabButton} ${activeTab === tab.id ? styles.tabActive : ''}`}
              onClick={() => onTabChange(tab.id)}
            >
              <span className={styles.tabIcon}>{tab.icon}</span>
              <span className={styles.tabLabel}>{tab.label}</span>
            </button>
          ))}
        </nav>

        {summaryMetrics && (
          <div className={styles.quickStatsPill}>
            <div className={styles.quickStatItem}>
              <span className={styles.quickStatLabel}>Preserved Bays:</span>
              <span className={styles.quickStatValue}>
                {summaryMetrics.pct_capacity_preserved ? `${summaryMetrics.pct_capacity_preserved}%` : '>91%'}
              </span>
              <div className={styles.quickStatTooltip}>
                Overall proportion of on-street parking capacity retained post-intervention across corridors.
              </div>
            </div>
            <div className={styles.statDivider}></div>
            <div className={styles.quickStatItem}>
              <span className={styles.quickStatLabel}>Avg Occupancy:</span>
              <span className={styles.quickStatValue}>
                {summaryMetrics.post_occupancy_pct ? `${summaryMetrics.post_occupancy_pct}%` : '6.6%'}
              </span>
              <div className={styles.quickStatTooltip}>
                Mean utilization percentage across remaining active bays during operational trading hours.
              </div>
            </div>
            <div className={styles.statDivider}></div>
            <div className={styles.quickStatItem}>
              <span className={styles.quickStatLabel}>Surplus Vacancy:</span>
              <span className={styles.quickStatValueGreen}>
                {summaryMetrics.surplus_vacancy_pct ? `>${summaryMetrics.surplus_vacancy_pct}%` : '>93%'}
              </span>
              <div className={styles.quickStatTooltip}>
                Proportion of active parking bays available and unoccupied during operational hours.
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;

