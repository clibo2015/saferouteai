import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import './NavigationBar.css';

const NavigationBar = ({ currentPage }) => {
  const location = useLocation();

  const navItems = [
    {
      id: 'dashboard',
      path: '/dashboard',
      icon: HomeIcon,
      label: 'Home',
    },
    {
      id: 'navigation',
      path: '/navigation',
      icon: NavigationIcon,
      label: 'Navigate',
    },
    {
      id: 'hazard',
      path: '/hazard-hud',
      icon: HazardIcon,
      label: 'Hazards',
    },
  ];

  return (
    <motion.div 
      className="navigation-bar"
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.5, duration: 0.6 }}
    >
      <div className="nav-container">
        {navItems.map((item, index) => {
          const isActive = location.pathname === item.path || currentPage === item.id;
          
          return (
            <NavItem
              key={item.id}
              item={item}
              isActive={isActive}
              index={index}
            />
          );
        })}
      </div>
      
      {/* Background blur effect */}
      <div className="nav-background" />
    </motion.div>
  );
};

const NavItem = ({ item, isActive, index }) => {
  return (
    <Link to={item.path} className="nav-item-link">
      <motion.div 
        className={`nav-item ${isActive ? 'active' : ''}`}
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.7 + index * 0.1, duration: 0.4 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <div className="nav-icon-container">
          <item.icon className="nav-icon" />
          {isActive && (
            <motion.div
              className="nav-indicator"
              layoutId="nav-indicator"
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            />
          )}
        </div>
        <span className="nav-label">{item.label}</span>
      </motion.div>
    </Link>
  );
};

// Icon Components
const HomeIcon = ({ className }) => (
  <svg className={className} width="24" height="24" viewBox="0 0 24 24" fill="none">
    <path
      d="M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M9 22V12H15V22"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const NavigationIcon = ({ className }) => (
  <svg className={className} width="24" height="24" viewBox="0 0 24 24" fill="none">
    <circle
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="2"
    />
    <path
      d="M16.24 7.76L14.12 14.12L7.76 16.24L9.88 9.88L16.24 7.76Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const HazardIcon = ({ className }) => (
  <svg className={className} width="24" height="24" viewBox="0 0 24 24" fill="none">
    <path
      d="M10.29 3.86L1.82 18C1.64466 18.3024 1.55611 18.6453 1.56331 18.9945C1.57051 19.3437 1.67319 19.6831 1.86 19.9784C2.04681 20.2737 2.31259 20.5141 2.62618 20.6747C2.93977 20.8352 3.28907 20.9099 3.64 20.89H20.36C20.7109 20.9099 21.0602 20.8352 21.3738 20.6747C21.6874 20.5141 21.9532 20.2737 22.14 19.9784C22.3268 19.6831 22.4295 19.3437 22.4367 18.9945C22.4439 18.6453 22.3553 18.3024 22.18 18L13.71 3.86C13.5317 3.56611 13.2807 3.32312 12.9812 3.15448C12.6817 2.98585 12.3438 2.89725 12 2.89725C11.6562 2.89725 11.3183 2.98585 11.0188 3.15448C10.7193 3.32312 10.4683 3.56611 10.29 3.86V3.86Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M12 9V13"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M12 17H12.01"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export default NavigationBar;