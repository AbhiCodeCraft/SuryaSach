export interface SystemWrite {
  capacity_kw: number;
  location_label: string;
  latitude: number;
  longitude: number;
  install_date: string | null;
  install_year: number | null;
  azimuth_degrees: number | null;
  tilt_degrees: number | null;
  vendor_name: string | null;
}

export interface SolarSystem extends SystemWrite {
  system_id: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}
