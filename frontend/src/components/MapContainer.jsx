import React, { useState, useEffect, useMemo, useRef } from 'react';
import Map, { Source, Layer, Popup } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import styles from './MapContainer.module.css';

const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

const INITIAL_VIEW_STATE = {
  latitude: -37.8115,
  longitude: 144.9570,
  zoom: 15.5,
  pitch: 45,
  bearing: 0
};

const getAllCoordinates = (geoJson) => {
  if (!geoJson || !geoJson.features) return [];
  const coords = [];
  const extract = (arr) => {
    if (!Array.isArray(arr) || arr.length === 0) return;
    if (typeof arr[0] === 'number' && typeof arr[1] === 'number') {
      coords.push(arr);
    } else {
      arr.forEach(extract);
    }
  };
  geoJson.features.forEach(f => {
    if (f.geometry && f.geometry.coordinates) {
      extract(f.geometry.coordinates);
    }
  });
  return coords;
};

const MapContainer = ({ blocksGeoJson, loading, onBlockClick, selectedBlock, selectedStreet, selectedSuburb }) => {
  const [hoverInfo, setHoverInfo] = useState(null);
  const mapRef = useRef(null);

  const hoverBlockDesc = hoverInfo?.properties?.block_desc || null;

  // Fit bounds when blocksGeoJson changes (new street selected)
  useEffect(() => {
    if (blocksGeoJson && blocksGeoJson.features && blocksGeoJson.features.length > 0 && mapRef.current) {
      const coords = getAllCoordinates(blocksGeoJson);
      if (coords.length > 0) {
        let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity;
        coords.forEach(([lng, lat]) => {
          if (lng < minLng) minLng = lng;
          if (lat < minLat) minLat = lat;
          if (lng > maxLng) maxLng = lng;
          if (lat > maxLat) maxLat = lat;
        });

        if (minLng !== Infinity && maxLng !== -Infinity) {
          mapRef.current.getMap().fitBounds(
            [[minLng, minLat], [maxLng, maxLat]],
            { 
              padding: { top: 195, bottom: 80, left: 80, right: 460 }, 
              duration: 1200 
            }
          );
        }
      }
    }
  }, [blocksGeoJson]);

  // Casing glow layer for high visibility
  const casingLayerStyle = useMemo(() => ({
    id: 'bike-lanes-casing',
    type: 'line',
    paint: {
      'line-color': [
        'case',
        ['==', ['get', 'block_desc'], selectedBlock || ''],
        '#ea580c', // Darker orange glow for selected block
        '#0284c7'  // Deep cyan glow for active street
      ],
      'line-width': [
        'case',
        ['==', ['get', 'block_desc'], selectedBlock || ''],
        12,
        8
      ],
      'line-blur': 3,
      'line-opacity': 0.65
    },
    layout: {
      'line-cap': 'round',
      'line-join': 'round'
    }
  }), [selectedBlock]);

  // Main vibrant line layer
  const layerStyle = useMemo(() => ({
    id: 'bike-lanes',
    type: 'line',
    paint: {
      'line-color': [
        'case',
        ['==', ['get', 'block_desc'], selectedBlock || ''],
        '#f97316', // Electric Orange for selected block
        ['==', ['get', 'block_desc'], hoverBlockDesc || ''],
        '#38bdf8', // Bright Light Cyan for hover
        '#06b6d4'  // Electric Cyan
      ],
      'line-width': [
        'case',
        ['==', ['get', 'block_desc'], selectedBlock || ''],
        7,
        ['==', ['get', 'block_desc'], hoverBlockDesc || ''],
        6,
        4.5
      ],
      'line-opacity': 0.95
    },
    layout: {
      'line-cap': 'round',
      'line-join': 'round'
    }
  }), [selectedBlock, hoverBlockDesc]);

  const onClick = (event) => {
    const feature = event.features && event.features[0];
    if (feature) {
      onBlockClick(feature.properties.block_desc);
    } else {
      onBlockClick(null);
    }
  };

  const onHover = (event) => {
    const { features, lngLat } = event;
    const hoveredFeature = features && features[0];

    if (hoveredFeature) {
      setHoverInfo({
        lng: lngLat.lng,
        lat: lngLat.lat,
        properties: hoveredFeature.properties
      });
    } else {
      setHoverInfo(null);
    }
  };

  return (
    <div className={styles.mapWrapper}>
      {loading && (
        <div className={styles.loadingOverlay}>
          <div className={styles.spinner}></div>
          <p>Processing spatial layers...</p>
        </div>
      )}

      {selectedStreet && (
        <div className={styles.streetFocusBadge}>
          <span className={styles.badgePulse}></span>
          <span className={styles.badgeText}>
            Visualizing Street: <strong>{selectedStreet}</strong> {selectedSuburb && <span className={styles.badgeSuburb}>({selectedSuburb})</span>}
          </span>
        </div>
      )}

      {/* Map Legend */}
      <div className={styles.mapLegend}>
        <div className={styles.legendTitle}>Map Legend</div>
        <div className={styles.legendItem}>
          <span className={styles.legendLineCyan}></span>
          <span className={styles.hasTooltip}>
            Bike Lane Segment
            <div className={styles.tooltipText}>
              <div className={styles.tooltipTitle}>Spatial Specs</div>
              <ul className={styles.tooltipList}>
                <li>Source: Transport Victoria BIN</li>
                <li>Mapped via 20m buffer to parking bays</li>
                <li>Dissolved into unified block features</li>
              </ul>
            </div>
          </span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendLineOrange}></span>
          <span className={`${styles.hasTooltip} ${styles.hasTooltipOrange}`}>
            Selected Segment
            <div className={`${styles.tooltipText} ${styles.tooltipOrange}`}>
              <div className={styles.tooltipTitle}>Active Selection</div>
              <ul className={styles.tooltipList}>
                <li>Currently highlighted street block</li>
                <li>Drives granular metrics in side panel</li>
              </ul>
            </div>
          </span>
        </div>
      </div>
      
      <Map
        ref={mapRef}
        initialViewState={INITIAL_VIEW_STATE}
        mapStyle={MAP_STYLE}
        onClick={onClick}
        onHover={onHover}
        interactiveLayerIds={['bike-lanes']}
        cursor={hoverInfo ? 'pointer' : 'default'}
      >
        {blocksGeoJson && (
          <Source type="geojson" data={blocksGeoJson}>
            <Layer {...casingLayerStyle} />
            <Layer {...layerStyle} />
          </Source>
        )}

        {hoverInfo && (
          <Popup
            longitude={hoverInfo.lng}
            latitude={hoverInfo.lat}
            closeButton={false}
            closeOnClick={false}
            anchor="bottom"
            offset={10}
          >
            <div className={styles.popupContent}>
              <div className={styles.popupTitle}>Bike Lane: {hoverInfo.properties.block_desc}</div>
              <div className={styles.popupStat}>
                Bays Removed: <span>{hoverInfo.properties.bays_removed}</span>
              </div>
              <div className={styles.popupStat}>
                Active Bays: <span>{hoverInfo.properties.final_bays}</span>
              </div>
              <div className={styles.popupStat}>
                Occupancy: <span>{hoverInfo.properties.post_occupancy ? `${(hoverInfo.properties.post_occupancy * 100).toFixed(1)}%` : 'N/A'}</span>
              </div>
            </div>
          </Popup>
        )}
      </Map>
    </div>
  );
};

export default MapContainer;
