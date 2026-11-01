import React, { useState, useEffect } from 'react';
import { X, Edit3, Compass, Zap, MapPin, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import { updateSurveyObservations } from '../services/surveyApi';

export default function SurveyObservationModal({ isOpen, onClose, onSuccess, survey }) {
  const [roofArea, setRoofArea] = useState('');
  const [shadowFreeArea, setShadowFreeArea] = useState('');
  const [roofOrientation, setRoofOrientation] = useState('SOUTH');
  const [roofTilt, setRoofTilt] = useState('15');
  const [roofStructure, setRoofStructure] = useState('FLUSH');
  const [existingPhase, setExistingPhase] = useState('SINGLE_PHASE');
  const [sanctionedLoad, setSanctionedLoad] = useState('');
  const [gpsLatitude, setGpsLatitude] = useState('');
  const [gpsLongitude, setGpsLongitude] = useState('');
  const [feasibility, setFeasibility] = useState('FEASIBLE');
  const [remarks, setRemarks] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && survey) {
      setError(null);
      setRoofArea(survey.roof_area_sqft !== null && survey.roof_area_sqft !== undefined ? String(survey.roof_area_sqft) : '');
      setShadowFreeArea(survey.shadow_free_area_sqft !== null && survey.shadow_free_area_sqft !== undefined ? String(survey.shadow_free_area_sqft) : '');
      setRoofOrientation(survey.roof_orientation || 'SOUTH');
      setRoofTilt(survey.roof_tilt_degrees !== null && survey.roof_tilt_degrees !== undefined ? String(survey.roof_tilt_degrees) : '15');
      setRoofStructure(survey.roof_structure_type || 'FLUSH');
      setExistingPhase(survey.existing_phase || 'SINGLE_PHASE');
      setSanctionedLoad(survey.sanctioned_load_kw !== null && survey.sanctioned_load_kw !== undefined ? String(survey.sanctioned_load_kw) : '');
      setGpsLatitude(survey.gps_latitude !== null && survey.gps_latitude !== undefined ? String(survey.gps_latitude) : '');
      setGpsLongitude(survey.gps_longitude !== null && survey.gps_longitude !== undefined ? String(survey.gps_longitude) : '');
      setFeasibility(survey.technical_feasibility || 'FEASIBLE');
      setRemarks(survey.remarks || '');
    }
  }, [isOpen, survey]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const rArea = parseFloat(roofArea);
    const sfArea = parseFloat(shadowFreeArea);

    if (isNaN(rArea) || rArea <= 0) {
      setError('Total roof area must be a positive number (> 0 sqft).');
      return;
    }
    if (isNaN(sfArea) || sfArea < 0) {
      setError('Shadow-free area must be zero or a positive number (>= 0 sqft).');
      return;
    }
    if (sfArea > rArea) {
      setError(`Shadow-free area (${sfArea} sqft) cannot exceed total roof area (${rArea} sqft).`);
      return;
    }

    const tilt = parseFloat(roofTilt);
    if (!isNaN(tilt) && (tilt < 0 || tilt > 90)) {
      setError('Roof tilt must be between 0 and 90 degrees.');
      return;
    }

    if (gpsLatitude) {
      const lat = parseFloat(gpsLatitude);
      if (isNaN(lat) || lat < -90 || lat > 90) {
        setError('GPS Latitude must be between -90 and 90 degrees.');
        return;
      }
    }

    if (gpsLongitude) {
      const lon = parseFloat(gpsLongitude);
      if (isNaN(lon) || lon < -180 || lon > 180) {
        setError('GPS Longitude must be between -180 and 180 degrees.');
        return;
      }
    }

    setSubmitting(true);
    try {
      const payload = {
        roof_area_sqft: rArea,
        shadow_free_area_sqft: sfArea,
        roof_orientation: roofOrientation,
        roof_tilt_degrees: !isNaN(tilt) ? tilt : undefined,
        roof_structure_type: roofStructure,
        existing_phase: existingPhase,
        sanctioned_load_kw: sanctionedLoad ? parseFloat(sanctionedLoad) : undefined,
        gps_latitude: gpsLatitude ? parseFloat(gpsLatitude) : undefined,
        gps_longitude: gpsLongitude ? parseFloat(gpsLongitude) : undefined,
        technical_feasibility: feasibility,
        remarks: remarks.trim() || undefined,
      };

      await updateSurveyObservations(survey.id, payload);
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to update technical observations');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen || !survey) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <Edit3 className="w-5 h-5 text-amber-500" />
            <div>
              <h3 className="font-bold text-base tracking-tight">Record Site Observations</h3>
              <p className="text-xs text-amber-400 font-mono">{survey.survey_number} • Status: {survey.status}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Form Body */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-5">
          {error && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Section 1: Rooftop Dimensions & Shadow Analysis */}
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2.5 flex items-center gap-1.5 text-amber-600">
              <Compass className="w-4 h-4" /> 1. Rooftop Area & Shadow Analysis
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Total Roof Area (sq ft) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={roofArea}
                  onChange={(e) => setRoofArea(e.target.value)}
                  placeholder="e.g. 600"
                  className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Shadow-Free Area (sq ft) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={shadowFreeArea}
                  onChange={(e) => setShadowFreeArea(e.target.value)}
                  placeholder="e.g. 520"
                  className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  required
                />
                <p className="text-[11px] text-slate-500 mt-1">Must not exceed total roof area.</p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Roof Orientation <span className="text-rose-500">*</span>
                </label>
                <select
                  value={roofOrientation}
                  onChange={(e) => setRoofOrientation(e.target.value)}
                  className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  required
                >
                  <option value="SOUTH">South (Optimal Yield)</option>
                  <option value="SOUTH_WEST">South-West</option>
                  <option value="SOUTH_EAST">South-East</option>
                  <option value="NORTH">North</option>
                  <option value="FLAT">Flat Rooftop</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Roof Pitch / Tilt (Degrees)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="90"
                  value={roofTilt}
                  onChange={(e) => setRoofTilt(e.target.value)}
                  placeholder="e.g. 15.0"
                  className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Civil & Structural Mounting */}
          <div className="pt-2 border-t border-slate-100">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2.5 flex items-center gap-1.5 text-amber-600">
              <Zap className="w-4 h-4" /> 2. Mounting Structure & Electrical Infrastructure
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Structure Type <span className="text-rose-500">*</span>
                </label>
                <select
                  value={roofStructure}
                  onChange={(e) => setRoofStructure(e.target.value)}
                  className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  required
                >
                  <option value="FLUSH">Flush Mount (Flat RCC / Terrace)</option>
                  <option value="ELEVATED">Elevated Superstructure (&gt; 6ft clearance)</option>
                  <option value="TIN_SHED">Tin / Industrial Sheet Profile</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Electrical Meter Phase <span className="text-rose-500">*</span>
                </label>
                <select
                  value={existingPhase}
                  onChange={(e) => setExistingPhase(e.target.value)}
                  className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  required
                >
                  <option value="SINGLE_PHASE">Single Phase (1-Phase, 230V)</option>
                  <option value="THREE_PHASE">Three Phase (3-Phase, 415V)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Sanctioned Load from Meter (kW)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={sanctionedLoad}
                  onChange={(e) => setSanctionedLoad(e.target.value)}
                  placeholder="e.g. 5.0"
                  className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Technical Feasibility Sign-off <span className="text-rose-500">*</span>
                </label>
                <select
                  value={feasibility}
                  onChange={(e) => setFeasibility(e.target.value)}
                  className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 bg-white font-semibold focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  required
                >
                  <option value="FEASIBLE" className="text-emerald-700">FEASIBLE (Good Solar Access)</option>
                  <option value="CONDITIONAL" className="text-amber-700">CONDITIONAL (Requires Structure/Civil Work)</option>
                  <option value="NOT_FEASIBLE" className="text-rose-700">NOT FEASIBLE (Excessive Shadow/Unsafe Roof)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Section 3: GPS Coordinates & Findings */}
          <div className="pt-2 border-t border-slate-100">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2.5 flex items-center gap-1.5 text-amber-600">
              <MapPin className="w-4 h-4" /> 3. GPS Coordinates & Observations
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  GPS Latitude
                </label>
                <input
                  type="number"
                  step="0.0000001"
                  min="-90"
                  max="90"
                  value={gpsLatitude}
                  onChange={(e) => setGpsLatitude(e.target.value)}
                  placeholder="e.g. 12.9715987"
                  className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 font-mono focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  GPS Longitude
                </label>
                <input
                  type="number"
                  step="0.0000001"
                  min="-180"
                  max="180"
                  value={gpsLongitude}
                  onChange={(e) => setGpsLongitude(e.target.value)}
                  placeholder="e.g. 77.5945627"
                  className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 font-mono focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>
            </div>

            <div className="mt-3">
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Technical Survey Observations & Surveyor Recommendations
              </label>
              <textarea
                rows={3}
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                placeholder="Detailed findings regarding cable routing, inverter placement, parapet wall height, tree pruning required..."
                className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-3 flex items-center justify-end gap-3 border-t border-slate-100 shrink-0">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-lg text-sm font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition shadow-sm flex items-center gap-1.5 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  <span>Saving Observations...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Save Observations</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
