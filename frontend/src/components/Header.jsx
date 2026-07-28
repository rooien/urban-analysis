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
      <label>{label}</label>
      <div 
        className={`${styles.glassSelectValue} ${disabled ? styles.disabled : ''} ${isOpen ? styles.active : ''}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        data-testid={`${label.toLowerCase()}-select`}
      >
        <span>{value || 'Select...'}</span>
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          width="16" 
          height="16" 
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

const Header = ({ 
  suburbs = [], 
  selectedSuburb, 
  selectedStreet, 
  onSuburbChange, 
  onStreetChange 
}) => {
  const currentSuburb = suburbs.find(s => s.name === selectedSuburb);
  const streets = currentSuburb ? ['All Streets', ...currentSuburb.streets] : [];

  return (
    <header className={styles.headerContainer} id="app-header">
      <div className={styles.titleSection}>
        <h1>Urban Mobility Impact</h1>
        <p>Parking Utilization vs Bike Lane Infrastructure</p>
      </div>
      <div className={styles.controls}>
        <CustomSelect 
          label="Suburb" 
          value={selectedSuburb} 
          options={suburbs.map(s => s.name)} 
          onChange={onSuburbChange} 
        />
        
        <CustomSelect 
          label="Street" 
          value={selectedStreet} 
          options={streets} 
          onChange={onStreetChange} 
          disabled={streets.length === 0}
        />
      </div>
    </header>
  );
};

export default Header;
