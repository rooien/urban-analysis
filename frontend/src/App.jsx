import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ExecutiveBriefing from './components/ExecutiveBriefing';
import MapContainer from './components/MapContainer';
import ImpactDashboard from './components/ImpactDashboard';

const API_PORT = import.meta.env.VITE_API_PORT || '7000';
const API_BASE_URL = `http://localhost:${API_PORT}`;

function App() {
  const [locations, setLocations] = useState([]);
  const [selectedSuburb, setSelectedSuburb] = useState('');
  const [selectedStreet, setSelectedStreet] = useState('');
  const [activeTab, setActiveTab] = useState('briefing');
  const [blocksGeoJson, setBlocksGeoJson] = useState(null);
  const [selectedBlock, setSelectedBlock] = useState(null);
  const [executiveData, setExecutiveData] = useState(null);
  const [hourlyData, setHourlyData] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch supported locations on mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/locations`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success' && data.suburbs.length > 0) {
          setLocations(data.suburbs);
          
          // Default to Melbourne (CBD) and La Trobe Street if available
          const cbd = data.suburbs.find(s => s.name === 'Melbourne (CBD)');
          if (cbd && cbd.streets.includes('La Trobe Street')) {
            setSelectedSuburb('Melbourne (CBD)');
            setSelectedStreet('La Trobe Street');
          } else {
            setSelectedSuburb(data.suburbs[0].name);
            setSelectedStreet(data.suburbs[0].streets[0]);
          }
        }
      })
      .catch(err => console.error('Error fetching locations:', err));
  }, []);

  // Update selected street when suburb changes
  const handleSuburbChange = (suburb) => {
    setSelectedSuburb(suburb);
    setSelectedStreet('All Streets');
    setSelectedBlock(null);
  };

  // Fetch Executive Summary and Hourly Data when filters change
  useEffect(() => {
    if (!selectedSuburb) return;
    
    let execUrl = `${API_BASE_URL}/api/executive-summary?suburb=${encodeURIComponent(selectedSuburb)}`;
    let occUrl = `${API_BASE_URL}/api/blocks/occupancy?suburb=${encodeURIComponent(selectedSuburb)}`;
    
    if (selectedStreet && selectedStreet !== 'All Streets') {
      execUrl += `&street=${encodeURIComponent(selectedStreet)}`;
      occUrl += `&street=${encodeURIComponent(selectedStreet)}`;
    }

    Promise.all([
      fetch(execUrl).then(r => r.json()),
      fetch(occUrl).then(r => r.json())
    ])
      .then(([execRes, occRes]) => {
        if (execRes.status === 'success') {
          setExecutiveData(execRes);
        }
        if (occRes.status === 'success') {
          setHourlyData(occRes.data);
        }
      })
      .catch(err => console.error('Error fetching executive metrics:', err));
  }, [selectedSuburb, selectedStreet]);

  // Fetch blocks GeoJSON for Map Explorer
  useEffect(() => {
    if (!selectedSuburb) return;
    
    setLoading(true);
    setBlocksGeoJson(null);
    setSelectedBlock(null);
    
    let url = `${API_BASE_URL}/api/blocks?suburb=${encodeURIComponent(selectedSuburb)}`;
    if (selectedStreet && selectedStreet !== 'All Streets') {
      url += `&street=${encodeURIComponent(selectedStreet)}`;
    }
    
    fetch(url)
      .then(res => res.json())
      .then(data => {
        if (data.type === 'FeatureCollection') {
          setBlocksGeoJson(data);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching blocks:', err);
        setLoading(false);
      });
  }, [selectedSuburb, selectedStreet]);

  // Update document title dynamically
  useEffect(() => {
    if (selectedSuburb) {
      const streetLabel = selectedStreet && selectedStreet !== 'All Streets' ? selectedStreet : selectedSuburb;
      document.title = `${streetLabel} Bike Lanes | Executive Urban Planning`;
    } else {
      document.title = 'Victoria Urban Planning - Executive Analytics';
    }
  }, [selectedSuburb, selectedStreet]);

  const handleBlockClick = (blockDesc) => {
    setSelectedBlock(blockDesc);
  };

  const handleSelectCorridor = (corridor) => {
    if (corridor.suburb) setSelectedSuburb(corridor.suburb);
    if (corridor.street) setSelectedStreet(corridor.street);
    if (corridor.fullDesc) setSelectedBlock(corridor.fullDesc);
    setActiveTab('explorer');
  };

  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden', position: 'relative' }}>
      <Header 
        suburbs={locations}
        selectedSuburb={selectedSuburb}
        selectedStreet={selectedStreet}
        onSuburbChange={handleSuburbChange}
        onStreetChange={setSelectedStreet}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        summaryMetrics={executiveData?.metrics}
      />
      
      {activeTab === 'briefing' && (
        <ExecutiveBriefing 
          executiveData={executiveData}
          hourlyData={hourlyData}
          onSelectCorridor={handleSelectCorridor}
        />
      )}

      {activeTab === 'explorer' && (
        <>
          <MapContainer 
            blocksGeoJson={blocksGeoJson}
            loading={loading}
            onBlockClick={handleBlockClick}
            selectedBlock={selectedBlock}
            selectedStreet={selectedStreet}
            selectedSuburb={selectedSuburb}
          />
          <ImpactDashboard 
            suburb={selectedSuburb}
            street={selectedStreet}
            selectedBlock={selectedBlock}
            onBlockClick={handleBlockClick}
            blocksGeoJson={blocksGeoJson}
          />
        </>
      )}
    </div>
  );
}

export default App;
