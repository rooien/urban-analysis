import React, { useState, useEffect } from 'react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend,
  BarChart,
  Bar
} from 'recharts';
import styles from './ImpactDashboard.module.css';

const API_PORT = import.meta.env.VITE_API_PORT || '8000';
const API_BASE_URL = `http://localhost:${API_PORT}`;
const BASELINE_YEAR = import.meta.env.VITE_BASELINE_YEAR || '2013';
const POST_YEAR = import.meta.env.VITE_POST_YEAR || '2014';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className={styles.customTooltip}>
        <p className={styles.tooltipLabel}>{`${label}:00`}</p>
        {payload.map((entry, index) => (
          <p key={index} className={styles.tooltipItem} style={{ color: entry.color }}>
            {entry.name}: {entry.value !== null ? `${(entry.value * 100).toFixed(1)}%` : 'No Data'}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const KPI_TOOLTIPS_BLOCK = {
  removed: `On-street parking bays removed on this specific block to accommodate the bike lane.`,
  active: `Active on-street parking bays remaining on this block.`,
  preOcc: `Average parking occupancy rate on this block during the baseline year (${BASELINE_YEAR}) before bike lanes.`,
  postOcc: `Average parking occupancy rate on this block's remaining bays during the post-installation year (${POST_YEAR}).`
};

const KPI_TOOLTIPS_OVERVIEW = {
  removed: `Total on-street parking bays removed across the selected area to accommodate bike lanes.`,
  active: `Total on-street parking bays that remain available for use across the selected area.`,
  preOcc: `Average parking occupancy rate across all blocks in this area during the baseline year (${BASELINE_YEAR}).`,
  postOcc: `Average parking occupancy rate across all blocks' remaining bays in the post-installation year (${POST_YEAR}).`
};

const KpiLabel = ({ label, tooltip }) => {
  return (
    <div className={styles.kpiLabel}>
      {label}
      <svg viewBox="0 0 24 24" className={styles.infoIcon} aria-hidden="true">
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none"/>
        <path d="M12 16v-4M12 8h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      </svg>
      <div className={styles.tooltip}>
        {tooltip}
      </div>
    </div>
  );
};

const ImpactDashboard = ({ suburb, street, selectedBlock, onBlockClick, blocksGeoJson }) => {
  const [occupancyData, setOccupancyData] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch hourly data when a block is selected
  useEffect(() => {
    if (!selectedBlock) {
      setOccupancyData([]);
      return;
    }

    setLoading(true);
    fetch(`${API_BASE_URL}/api/blocks/occupancy?suburb=${encodeURIComponent(suburb)}&street=${encodeURIComponent(street)}&block_desc=${encodeURIComponent(selectedBlock)}`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setOccupancyData(data.data);
        } else {
          setOccupancyData([]);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching occupancy:', err);
        setOccupancyData([]);
        setLoading(false);
      });
  }, [suburb, street, selectedBlock]);

  // Compute Aggregated Overview Stats
  const overviewStats = React.useMemo(() => {
    if (!blocksGeoJson || !blocksGeoJson.features) return null;
    
    let baseline = 0;
    let final = 0;
    let preOccSum = 0;
    let postOccSum = 0;
    let countPre = 0;
    let countPost = 0;
    
    const chartData = [];

    blocksGeoJson.features.forEach(f => {
      const p = f.properties;
      baseline += p.baseline_bays || 0;
      final += p.final_bays || 0;
      
      if (p.pre_occupancy !== null) {
        preOccSum += p.pre_occupancy;
        countPre++;
      }
      if (p.post_occupancy !== null) {
        postOccSum += p.post_occupancy;
        countPost++;
      }

      if (p.bays_removed > 0) {
        // Format block descriptions for clean, professional chart labels
        let formattedName = p.block_desc;
        const match = p.block_desc.match(/(.+) (?:between|from) (.+?)(?: and | to |$)/i);
        if (match) {
          const st = match[1].replace(/ Street/g, ' St');
          const cross1 = match[2].replace(/ Street/g, ' St');
          if (street && street !== 'All Streets') {
            formattedName = cross1;
          } else {
            formattedName = `${st} @ ${cross1}`;
          }
        } else {
          formattedName = p.block_desc.replace(/ Street/g, ' St');
        }
        
        chartData.push({
          name: formattedName,
          removed: p.bays_removed
        });
      }
    });

    // Sort by most removed
    chartData.sort((a, b) => b.removed - a.removed);

    return {
      baseline,
      final,
      removed: baseline - final,
      preOcc: countPre > 0 ? preOccSum / countPre : 0,
      postOcc: countPost > 0 ? postOccSum / countPost : 0,
      chartData: chartData.slice(0, 5) // Top 5
    };
  }, [blocksGeoJson, street]);

  // Selected Block properties
  const selectedProperties = React.useMemo(() => {
    if (!selectedBlock || !blocksGeoJson) return null;
    const f = blocksGeoJson.features.find(f => f.properties.block_desc === selectedBlock);
    return f ? f.properties : null;
  }, [selectedBlock, blocksGeoJson]);

  if (!overviewStats) return null;

  return (
    <div className={styles.dashboardPanel}>
      {selectedBlock ? (
        <>
          <button className={styles.closeButton} onClick={() => onBlockClick(null)}>×</button>

          <div className={styles.questionContainer}>
            <div className={styles.questionBadge}>Core Research Question</div>
            <h2 className={styles.questionText}>
              How does parking use change with bike lanes constructed on {selectedBlock}?
            </h2>
          </div>

          {selectedProperties && (() => {
            const baseline = selectedProperties.baseline_bays || 0;
            const removed = selectedProperties.bays_removed || 0;
            const pctRemoved = baseline > 0 ? Math.round((removed / baseline) * 100) : 0;
            
            const pre = selectedProperties.pre_occupancy;
            const post = selectedProperties.post_occupancy;
            const hasData = pre !== null && post !== null;
            const diff = hasData ? post - pre : 0;
            const isPositive = diff > 0;
            
            return (
              <div className={`${styles.directAnswerCard} ${isPositive ? styles.positiveEffect : ''}`}>
                <div className={styles.directAnswerTitle}>Direct Answer & Findings</div>
                <div className={styles.answerHeadline}>
                  {removed === 0 ? (
                    "No parking bays were removed on this block for bike lanes."
                  ) : (
                    <>
                      Constructing bike lanes removed <span className={styles.highlightAlert}>{removed} parking bays</span> ({pctRemoved}% capacity reduction). Average parking occupancy on remaining bays <span className={styles.highlightAlert}>{isPositive ? `increased by +${(diff * 100).toFixed(1)}%` : diff < 0 ? `decreased by ${(diff * 100).toFixed(1)}%` : 'remained unchanged'}</span>.
                    </>
                  )}
                </div>
                <ul className={styles.answerPoints}>
                  <li className={styles.answerPoint}>
                    <span className={styles.answerIcon}>🚴</span>
                    <div>
                      <strong>Capacity Impact:</strong> {removed} bays removed ({pctRemoved}% reduction)
                    </div>
                  </li>
                  <li className={styles.answerPoint}>
                    <span className={styles.answerIcon}>🅿️</span>
                    <div>
                      <strong>Occupancy Shift:</strong> {pre !== null ? `${(pre * 100).toFixed(1)}%` : 'N/A'} ({BASELINE_YEAR}) → {post !== null ? `${(post * 100).toFixed(1)}%` : 'N/A'} ({POST_YEAR})
                    </div>
                  </li>
                  <li className={styles.answerPoint}>
                    <span className={styles.answerIcon}>📊</span>
                    <div>
                      <strong>Net Effect:</strong> {
                        removed === 0 ? 'Capacity unchanged on this segment.' :
                        isPositive ? 'Higher occupancy pressure on remaining active bays.' :
                        'Reduced occupancy rate on remaining bays.'
                      }
                    </div>
                  </li>
                </ul>
              </div>
            );
          })()}

          {selectedProperties && (
            <div className={styles.kpiGrid}>
              <div className={styles.kpiCard}>
                <KpiLabel label="Bays Removed" tooltip={KPI_TOOLTIPS_BLOCK.removed} />
                <div className={styles.kpiValueOrange}>{selectedProperties.bays_removed}</div>
              </div>
              <div className={styles.kpiCard}>
                <KpiLabel label="Active Bays" tooltip={KPI_TOOLTIPS_BLOCK.active} />
                <div className={styles.kpiValue}>{selectedProperties.final_bays}</div>
              </div>
              <div className={styles.kpiCard}>
                <KpiLabel label="Pre-Occupancy" tooltip={KPI_TOOLTIPS_BLOCK.preOcc} />
                <div className={styles.kpiValue}>
                  {selectedProperties.pre_occupancy ? `${(selectedProperties.pre_occupancy * 100).toFixed(1)}%` : 'N/A'}
                </div>
              </div>
              <div className={styles.kpiCard}>
                <KpiLabel label="Post-Occupancy" tooltip={KPI_TOOLTIPS_BLOCK.postOcc} />
                <div className={styles.kpiValue}>
                  {selectedProperties.post_occupancy ? `${(selectedProperties.post_occupancy * 100).toFixed(1)}%` : 'N/A'}
                </div>
              </div>
            </div>
          )}

          <div className={styles.chartSection}>
            <div className={styles.chartHeader}>Hourly Occupancy Profile ({BASELINE_YEAR} vs {POST_YEAR})</div>
            <div className={styles.chartContainer}>
              {loading ? (
                <div className={styles.loadingWrapper}>Loading hourly data...</div>
              ) : occupancyData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={occupancyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis 
                      dataKey="h" 
                      type="number"
                      domain={[0, 23]}
                      ticks={[0, 4, 8, 12, 16, 20]}
                      tickFormatter={h => `${h}:00`}
                      stroke="var(--text-muted)" 
                      fontSize={11}
                    />
                    <YAxis 
                      tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                      stroke="var(--text-muted)" 
                      fontSize={11}
                      domain={[0, 'auto']}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                    <Line 
                      type="monotone" 
                      dataKey="occ_pre" 
                      name={`${BASELINE_YEAR} (Pre-Lane)`} 
                      stroke="var(--text-secondary)" 
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="occ_post" 
                      name={`${POST_YEAR} (Post-Lane)`} 
                      stroke="var(--accent-coral)" 
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className={styles.loadingWrapper}>No hourly data available for this block.</div>
              )}
            </div>
          </div>
        </>
      ) : (
        <>
          <div className={styles.questionContainer}>
            <div className={styles.questionBadge}>Core Research Question</div>
            <h2 className={styles.questionText}>
              How does parking use change with bike lanes constructed in {suburb || 'this area'}{street && street !== 'All Streets' ? ` on ${street}` : ''}?
            </h2>
          </div>

          {(() => {
            const removed = overviewStats.removed;
            const total = overviewStats.baseline;
            const pct = total > 0 ? Math.round((removed / total) * 100) : 0;
            const pre = overviewStats.preOcc;
            const post = overviewStats.postOcc;
            const hasData = pre > 0 && post > 0;
            const diff = hasData ? post - pre : 0;
            const isPositive = diff > 0;
            
            return (
              <div className={`${styles.directAnswerCard} ${isPositive ? styles.positiveEffect : ''}`}>
                <div className={styles.directAnswerTitle}>Direct Answer & Findings</div>
                <div className={styles.answerHeadline}>
                  {removed === 0 ? (
                    `No parking bays were removed across ${street && street !== 'All Streets' ? street : suburb || 'this area'} for bike lanes.`
                  ) : (
                    <>
                      Constructing bike lanes in <span className={styles.highlightAlert}>{suburb}</span> {street && street !== 'All Streets' ? `on ${street}` : 'across all streets'} removed <span className={styles.highlightAlert}>{removed} parking bays</span> ({pct}% capacity reduction). Average parking occupancy <span className={styles.highlightAlert}>{isPositive ? `increased by +${(diff * 100).toFixed(1)}%` : diff < 0 ? `decreased by ${(diff * 100).toFixed(1)}%` : 'remained unchanged'}</span>.
                    </>
                  )}
                </div>
                <ul className={styles.answerPoints}>
                  <li className={styles.answerPoint}>
                    <span className={styles.answerIcon}>🚴</span>
                    <div>
                      <strong>Capacity Impact:</strong> {removed} total bays removed ({pct}% capacity reduction)
                    </div>
                  </li>
                  <li className={styles.answerPoint}>
                    <span className={styles.answerIcon}>🅿️</span>
                    <div>
                      <strong>Average Occupancy Shift:</strong> {pre > 0 ? `${(pre * 100).toFixed(1)}%` : 'N/A'} ({BASELINE_YEAR}) → {post > 0 ? `${(post * 100).toFixed(1)}%` : 'N/A'} ({POST_YEAR})
                    </div>
                  </li>
                  <li className={styles.answerPoint}>
                    <span className={styles.answerIcon}>📊</span>
                    <div>
                      <strong>Net Utilization Effect:</strong> {
                        isPositive ? 'Concentrated parking demand increased occupancy across remaining active bays.' :
                        'Overall on-street parking occupancy decreased following bike lane installation.'
                      }
                    </div>
                  </li>
                </ul>
              </div>
            );
          })()}

          <div className={styles.kpiGrid}>
            <div className={styles.kpiCard}>
              <KpiLabel label="Total Bays Removed" tooltip={KPI_TOOLTIPS_OVERVIEW.removed} />
              <div className={styles.kpiValueOrange}>{overviewStats.removed}</div>
            </div>
            <div className={styles.kpiCard}>
              <KpiLabel label="Remaining Bays" tooltip={KPI_TOOLTIPS_OVERVIEW.active} />
              <div className={styles.kpiValue}>{overviewStats.final}</div>
            </div>
            <div className={styles.kpiCard}>
              <KpiLabel label="Avg Pre-Occupancy" tooltip={KPI_TOOLTIPS_OVERVIEW.preOcc} />
              <div className={styles.kpiValue}>
                {overviewStats.preOcc > 0 ? `${(overviewStats.preOcc * 100).toFixed(1)}%` : 'N/A'}
              </div>
            </div>
            <div className={styles.kpiCard}>
              <KpiLabel label="Avg Post-Occupancy" tooltip={KPI_TOOLTIPS_OVERVIEW.postOcc} />
              <div className={styles.kpiValue}>
                {overviewStats.postOcc > 0 ? `${(overviewStats.postOcc * 100).toFixed(1)}%` : 'N/A'}
              </div>
            </div>
          </div>

          {overviewStats.chartData.length > 0 && (
            <div className={styles.chartSection}>
              <div className={styles.chartHeader}>Top Blocks by Bays Removed</div>
              <div className={styles.chartContainer}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart 
                    data={overviewStats.chartData} 
                    layout="vertical" 
                    margin={{ top: 0, right: 10, left: 120, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                    <XAxis stroke="var(--text-muted)" fontSize={11} type="number" />
                    <YAxis 
                      dataKey="name" 
                      type="category" 
                      stroke="var(--text-muted)" 
                      fontSize={10}
                      width={120}
                    />
                    <Tooltip 
                      cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                      formatter={(value) => [`${value} bays`, 'Removed']}
                      contentStyle={{ background: 'var(--bg-surface)', borderColor: 'var(--border-glass)', borderRadius: '4px' }}
                      itemStyle={{ color: 'var(--accent-coral)' }}
                    />
                    <Bar dataKey="removed" fill="var(--accent-coral)" radius={[0, 4, 4, 0]} barSize={16} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>📍</div>
            <p>Click any highlighted street segment on the map to drill into block-specific occupancy profiles.</p>
          </div>
        </>
      )}
    </div>
  );
};

export default ImpactDashboard;
