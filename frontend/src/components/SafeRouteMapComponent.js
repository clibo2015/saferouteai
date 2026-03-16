import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
    MapContainer,
    TileLayer,
    Marker,
    Popup,
    Polyline,
    Circle,
    LayerGroup,
    useMap,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './SafeRouteMapComponent.css';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/apiService';

// Components
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// =============================================================================
// SOUTH AFRICA CRIME HOTSPOT DATABASE — all 9 provinces (SAPS 2025/26)
// Level 1: Station/area level  |  Level 2: Street/intersection/building level
// Source: real_crime_hotspots_analysis.csv + SAPS 2025/26 annual report
// =============================================================================
const SA_CRIME_HOTSPOTS = [

    // ─── GAUTENG ─── Extreme/High (SAPS: 50%+ of national hijackings) ──────────

    // Jabulani station area
    { id: 'gt_jab', lat: -26.2678, lng: 27.8546, name: 'Jabulani SAPS Station', province: 'Gauteng', type: 'carjacking', risk: 0.93, label: 'SAPS Extreme — 983 hijackings/quarter', street: 'Jabulani Mall, Khumalo Rd, Soweto' },
    { id: 'gt_jab_s1', lat: -26.2654, lng: 27.8521, name: 'Khumalo St & Immink Dr', province: 'Gauteng', type: 'carjacking', risk: 0.92, label: 'Top carjacking intersection — Jabulani', street: 'Khumalo St & Immink Dr, Jabulani' },
    { id: 'gt_jab_s2', lat: -26.2701, lng: 27.8563, name: 'Jabulani Mall Parking', province: 'Gauteng', type: 'robbery', risk: 0.90, label: 'Shopping mall parking robbery', street: 'Jabulani Mall, Khumalo Rd' },
    { id: 'gt_jab_s3', lat: -26.2630, lng: 27.8600, name: 'Soweto Hwy N-bound ramp', province: 'Gauteng', type: 'hijacking', risk: 0.91, label: 'N12/Soweto Hwy truck hijacking', street: 'Soweto Hwy (N12) northbound off-ramp, Jabulani' },

    // Hillbrow — extreme robbery
    { id: 'gt_hbw', lat: -26.1833, lng: 28.0500, name: 'Hillbrow SAPS Station', province: 'Gauteng', type: 'robbery', risk: 0.96, label: 'SAPS Extreme — 3283 robberies/quarter', street: 'Kotze St, Hillbrow' },
    { id: 'gt_hbw_s1', lat: -26.1851, lng: 28.0515, name: 'Pretoria St & Claim St', province: 'Gauteng', type: 'mugging', risk: 0.95, label: 'Pedestrian mugging hotspot', street: 'Pretoria St & Claim St, Hillbrow' },
    { id: 'gt_hbw_s2', lat: -26.1879, lng: 28.0488, name: 'Edith Cavell St (Hillbrow Rd)', province: 'Gauteng', type: 'robbery', risk: 0.94, label: 'Street robbery after dark', street: 'Hillbrow Rd / Edith Cavell St, Hillbrow' },
    { id: 'gt_hbw_s3', lat: -26.1823, lng: 28.0532, name: 'Fontein & Edith Cavell', province: 'Gauteng', type: 'robbery', risk: 0.93, label: 'ATM robbery / mugging zone', street: 'Fontein St & Edith Cavell St, Hillbrow' },
    { id: 'gt_hbw_s4', lat: -26.1861, lng: 28.0553, name: 'Smit St Taxi Rank', province: 'Gauteng', type: 'robbery', risk: 0.90, label: 'Taxi rank robbery', street: 'Smit St Taxi Rank, Berea/Hillbrow' },
    { id: 'gt_hbw_s5', lat: -26.1899, lng: 28.0471, name: 'Kotze St & Abel Rd', province: 'Gauteng', type: 'robbery', risk: 0.92, label: 'Night robbery concentration', street: 'Kotze St & Abel Rd, Hillbrow' },

    // Joburg Central station
    { id: 'gt_jbc', lat: -26.2041, lng: 28.0473, name: 'Joburg Central SAPS', province: 'Gauteng', type: 'robbery', risk: 0.91, label: 'SAPS Extreme — 3283 robberies/quarter', street: 'Eloff St, Johannesburg CBD' },
    { id: 'gt_jbc_s1', lat: -26.2063, lng: 28.0440, name: 'Noord St Taxi Rank', province: 'Gauteng', type: 'robbery', risk: 0.93, label: 'Busiest taxi rank — high robbery', street: 'Noord St Taxi Rank, Johannesburg CBD' },
    { id: 'gt_jbc_s2', lat: -26.2018, lng: 28.0498, name: 'Park Station Surrounds', province: 'Gauteng', type: 'mugging', risk: 0.90, label: 'Pedestrian mugging & bag-snatching', street: 'Wolmarans St, near Park Station' },
    { id: 'gt_jbc_s3', lat: -26.2077, lng: 28.0388, name: 'Jeppe St & Von Brandis St', province: 'Gauteng', type: 'carjacking', risk: 0.88, label: 'CBD carjacking intersection', street: 'Jeppe St & Von Brandis St, JHB CBD' },
    { id: 'gt_jbc_s4', lat: -26.2023, lng: 28.0550, name: 'Bree St Market', province: 'Gauteng', type: 'robbery', risk: 0.87, label: 'Market area robbery/pickpocket', street: 'Bree St, Johannesburg CBD' },
    { id: 'gt_jbc_s5', lat: -26.2101, lng: 28.0428, name: 'President & Harrison St', province: 'Gauteng', type: 'robbery', risk: 0.85, label: 'Street robbery zone', street: 'President St & Harrison St, JHB CBD' },

    // Akasia station — carjacking
    { id: 'gt_aka', lat: -25.7488, lng: 28.1865, name: 'Akasia SAPS Station', province: 'Gauteng', type: 'carjacking', risk: 0.82, label: 'SAPS Extreme — 983 hijackings/quarter', street: 'Bauhinia St, Akasia, Pretoria North' },
    { id: 'gt_aka_s1', lat: -25.7331, lng: 28.1886, name: 'N1 North (Bela-Bela offramp)', province: 'Gauteng', type: 'hijacking', risk: 0.87, label: 'N1 truck hijacking corridor', street: 'N1 North near Bauhinia St off-ramp, Pretoria' },
    { id: 'gt_aka_s2', lat: -25.7510, lng: 28.2010, name: 'Soshanguve Highway ramp', province: 'Gauteng', type: 'carjacking', risk: 0.83, label: 'Off-ramp carjacking', street: 'Soshanguve Hwy off-ramp, Akasia' },

    // Tembisa station
    { id: 'gt_tem', lat: -25.9833, lng: 28.2333, name: 'Tembisa SAPS Station', province: 'Gauteng', type: 'carjacking', risk: 0.86, label: 'SAPS Extreme — 3283 crimes/quarter', street: 'Commissioner St, Tembisa' },
    { id: 'gt_tem_s1', lat: -25.9912, lng: 28.2289, name: 'R25 / Olifantsfontein Rd', province: 'Gauteng', type: 'carjacking', risk: 0.86, label: 'N14/R25 carjacking corridor', street: 'R25 Olifantsfontein Rd — Tembisa turnoff' },
    { id: 'gt_tem_s2', lat: -25.9766, lng: 28.2400, name: 'Tembisa Town Centre Taxi Rank', province: 'Gauteng', type: 'robbery', risk: 0.84, label: 'Taxi rank robbery & bag-snatching', street: 'Tembisa Town Centre, Main Rd Tembisa' },
    { id: 'gt_tem_s3', lat: -25.9870, lng: 28.2450, name: 'Isipingo Rd & Pretoria Rd', province: 'Gauteng', type: 'carjacking', risk: 0.83, label: 'Intersection carjacking', street: 'Isipingo Rd & Pretoria Rd, Tembisa' },

    // Ivory Park station
    { id: 'gt_ivo', lat: -26.0935, lng: 28.2215, name: 'Ivory Park SAPS Station', province: 'Gauteng', type: 'carjacking', risk: 0.93, label: 'SAPS Extreme — top carjacking station', street: 'Ivory Park, Midrand' },
    { id: 'gt_ivo_s1', lat: -26.0870, lng: 28.2330, name: 'Ivory Park Shopping — N14 ramp', province: 'Gauteng', type: 'carjacking', risk: 0.92, label: 'Mall approach carjacking', street: 'N14 on-ramp near Ivory Park Mall' },
    { id: 'gt_ivo_s2', lat: -26.0980, lng: 28.2250, name: 'Rabie Ridge intersection', province: 'Gauteng', type: 'hijacking', risk: 0.89, label: 'Truck hijacking node', street: 'Rabie Ridge Rd, Ivory Park' },

    // Extra Gauteng street spots
    { id: 'gt_alex_s1', lat: -26.1019, lng: 28.1048, name: 'Alexandra — Selbourne Rd', province: 'Gauteng', type: 'robbery', risk: 0.88, label: 'High robbery — pedestrian route', street: 'Selbourne Ave, Alexandra Township' },
    { id: 'gt_alex_s2', lat: -26.1060, lng: 28.1010, name: 'Pan Africa Shopping Centre', province: 'Gauteng', type: 'carjacking', risk: 0.85, label: 'Parking lot carjacking', street: 'Pan Africa Mall, Wynberg / Alexandra' },
    { id: 'gt_ekur_s1', lat: -26.3544, lng: 28.1575, name: 'Ekurhuleni N3 Truck Route', province: 'Gauteng', type: 'hijacking', risk: 0.83, label: 'N3 freight hijacking zone', street: 'N3 Southbound, Ekurhuleni near exits 10–14' },
    { id: 'gt_rand_s1', lat: -26.2442, lng: 28.1430, name: 'Germiston Lake Rd', province: 'Gauteng', type: 'carjacking', risk: 0.79, label: 'Carjacking — late-night route', street: 'Lake Rd, Germiston CBD' },

    // ─── WESTERN CAPE ─── High (morning-peak hijackings) ───────────────────────

    // Philippi East
    { id: 'wc_phi', lat: -34.0333, lng: 18.6167, name: 'Philippi East SAPS', province: 'Western Cape', type: 'carjacking', risk: 0.95, label: 'SAPS High — morning peak hijackings', street: 'Philippi Ave, Philippi East' },
    { id: 'wc_phi_s1', lat: -34.0290, lng: 18.6120, name: 'Philippi Ave & Vanguard Dr', province: 'Western Cape', type: 'carjacking', risk: 0.94, label: 'Top hijacking intersection WC', street: 'Philippi Ave & Vanguard Dr, Philippi' },
    { id: 'wc_phi_s2', lat: -34.0350, lng: 18.6200, name: 'Spine Rd Taxi Rank', province: 'Western Cape', type: 'robbery', risk: 0.90, label: 'Taxi rank mugging', street: 'Spine Rd Taxi Rank, Philippi East' },
    { id: 'wc_phi_s3', lat: -34.0375, lng: 18.6085, name: 'Cnr Lansdowne & Morgenster Rd', province: 'Western Cape', type: 'carjacking', risk: 0.92, label: 'High-frequency hijacking spot', street: 'Lansdowne Rd & Morgenster Rd, Philippi' },

    // Harare (Khayelitsha)
    { id: 'wc_har', lat: -34.0167, lng: 18.6000, name: 'Harare SAPS Station', province: 'Western Cape', type: 'carjacking', risk: 0.91, label: 'SAPS High — 291 hijackings/quarter', street: 'Harare, Khayelitsha' },
    { id: 'wc_har_s1', lat: -34.0212, lng: 18.5992, name: 'Steve Biko Rd & Mike Pienaar Blvd', province: 'Western Cape', type: 'carjacking', risk: 0.90, label: 'Khayelitsha hijacking intersection', street: 'Steve Biko Rd & Mike Pienaar Blvd, Khayelitsha' },
    { id: 'wc_har_s2', lat: -34.0155, lng: 18.6043, name: 'Khayelitsha Mall Entrance', province: 'Western Cape', type: 'robbery', risk: 0.88, label: 'Mall parking robbery', street: 'Khayelitsha Mall, Ntlazane Rd' },

    // Delft
    { id: 'wc_del', lat: -33.9833, lng: 18.6333, name: 'Delft SAPS Station', province: 'Western Cape', type: 'robbery', risk: 0.89, label: 'SAPS High — 291 hijackings/quarter', street: 'Delft South, Cape Town' },
    { id: 'wc_del_s1', lat: -33.9801, lng: 18.6388, name: 'Voorbrug & Komaan Rd Delft', province: 'Western Cape', type: 'robbery', risk: 0.88, label: 'Gang-related robbery intersection', street: 'Voorbrug Rd & Komaan Rd, Delft South' },
    { id: 'wc_del_s2', lat: -33.9865, lng: 18.6411, name: 'Delft Main Taxi Stop', province: 'Western Cape', type: 'mugging', risk: 0.85, label: 'Commuter mugging, bag-snatching', street: 'Baden Powell Dr, Delft Main' },

    // Cape Town Central
    { id: 'wc_ctc', lat: -33.9249, lng: 18.4241, name: 'Cape Town Central SAPS', province: 'Western Cape', type: 'robbery', risk: 0.81, label: 'SAPS High — 2250 robberies/quarter', street: 'Buitenkant St, Cape Town CBD' },
    { id: 'wc_ctc_s1', lat: -33.9249, lng: 18.4241, name: 'Long St at Night', province: 'Western Cape', type: 'mugging', risk: 0.82, label: 'Late-night mugging strip', street: 'Long St, Cape Town CBD' },
    { id: 'wc_ctc_s2', lat: -33.9206, lng: 18.4246, name: 'Cape Town Station (Adderley)', province: 'Western Cape', type: 'robbery', risk: 0.80, label: 'Platform / approach robbery', street: 'Adderley St, Cape Town Station' },
    { id: 'wc_ctc_s3', lat: -33.9300, lng: 18.4174, name: 'De Waal Dr on-ramp (M3)', province: 'Western Cape', type: 'carjacking', risk: 0.77, label: 'Carjacking on M3 on-ramp', street: 'De Waal Dr M3 on-ramp, Salt River side' },
    { id: 'wc_ctc_s4', lat: -33.9225, lng: 18.4333, name: 'Buitenkant & Searle St', province: 'Western Cape', type: 'robbery', risk: 0.79, label: 'Mugging — after-hours CBD fringe', street: 'Buitenkant St & Searle St, Cape Town' },

    // Mitchells Plain
    { id: 'wc_mp', lat: -34.0364, lng: 18.6106, name: 'Mitchells Plain SAPS', province: 'Western Cape', type: 'robbery', risk: 0.87, label: 'SAPS High — 2250 robberies/quarter', street: 'Cnr Freedom Way & Spine Rd, Mitchells Plain' },
    { id: 'wc_mp_s1', lat: -34.0320, lng: 18.6090, name: 'Freedom Way & AZ Berman Dr', province: 'Western Cape', type: 'carjacking', risk: 0.87, label: 'Hijacking intersection', street: 'Freedom Way & AZ Berman Dr, Mitchells Plain' },
    { id: 'wc_mp_s2', lat: -34.0411, lng: 18.6071, name: 'Westridge Shoprite Parking', province: 'Western Cape', type: 'robbery', risk: 0.84, label: 'Parking lot robbery — Shoprite', street: 'Westridge Gardens Mall, Mitchells Plain' },

    // Smaller WC street spots
    { id: 'wc_man_s1', lat: -33.9587, lng: 18.5592, name: 'Manenberg Ave (main stretch)', province: 'Western Cape', type: 'robbery', risk: 0.90, label: 'Gang territory — extreme risk', street: 'Manenberg Ave, Manenberg' },
    { id: 'wc_han_s1', lat: -34.0441, lng: 18.5756, name: 'Hanover Park — Thornton Rd', province: 'Western Cape', type: 'robbery', risk: 0.86, label: 'Gang robbery zone', street: 'Thornton Rd, Hanover Park' },
    { id: 'wc_kha_s1', lat: -34.0041, lng: 18.6800, name: 'Site B Shopping Centre', province: 'Western Cape', type: 'robbery', risk: 0.86, label: 'Parking lot robbery', street: 'Site B Shopping Centre, Khayelitsha' },

    // Stellenbosch — requested for testing
    { id: 'wc_stb_s1', lat: -33.9248, lng: 18.8465, name: 'Bird St & Adam Tas Rd', province: 'Western Cape', type: 'robbery', risk: 0.72, label: 'Moderate risk — evening mugging', street: 'Bird St & Adam Tas Rd, Stellenbosch' },
    { id: 'wc_stb_s2', lat: -33.9180, lng: 18.8350, name: 'Kayamandi Entrance', province: 'Western Cape', type: 'robbery', risk: 0.78, label: 'High robbery — commuter route', street: 'Kayamandi Entrance, Stellenbosch' },

    // ─── KWAZULU-NATAL ─── High (residential robbery) ──────────────────────────

    // Umlazi
    { id: 'kzn_uml', lat: -29.9689, lng: 30.8821, name: 'Umlazi SAPS Station', province: 'KZN', type: 'carjacking', risk: 0.93, label: 'SAPS High — 271 hijackings/quarter, street: "Mondi Rd, Umlazi"', street: 'Mondi Rd, Umlazi' },
    { id: 'kzn_uml_s1', lat: -29.9630, lng: 30.8910, name: 'B-Section — Higginson Hwy', province: 'KZN', type: 'carjacking', risk: 0.92, label: 'Umlazi B-Section hijacking', street: 'Higginson Hwy near B-Section, Umlazi' },
    { id: 'kzn_uml_s2', lat: -29.9750, lng: 30.8800, name: 'V-Section Taxi Rank Umlazi', province: 'KZN', type: 'robbery', risk: 0.89, label: 'Taxi rank robbery zone', street: 'V-Section Taxi Rank, Umlazi' },
    { id: 'kzn_uml_s3', lat: -29.9700, lng: 30.8750, name: 'KwaZulu Retail Park — Umlazi', province: 'KZN', type: 'robbery', risk: 0.87, label: 'Retail parking robbery', street: 'KwaZulu Retail Park, Umlazi' },

    // Durban Central
    { id: 'kzn_dbn', lat: -29.8587, lng: 31.0218, name: 'Durban Central SAPS', province: 'KZN', type: 'robbery', risk: 0.84, label: 'SAPS High — 1416 robberies/quarter', street: 'Anton Lembede St (Smith St), Durban CBD' },
    { id: 'kzn_dbn_s1', lat: -29.8608, lng: 31.0245, name: 'Grey St — Victoria St Market', province: 'KZN', type: 'robery', risk: 0.85, label: 'Market area robbery & mugging', street: 'Grey St & Victoria St Market, Durban CBD' },
    { id: 'kzn_dbn_s2', lat: -29.8560, lng: 31.0181, name: 'Durban Station — NMR Ave', province: 'KZN', type: 'robbery', risk: 0.83, label: 'Station area robbery', street: 'NMR Ave near Durban Station' },
    { id: 'kzn_dbn_s3', lat: -29.8545, lng: 31.0120, name: 'Warwick Ave Taxi Rank', province: 'KZN', type: 'robbery', risk: 0.86, label: 'Busiest taxi rank — robbery', street: 'Warwick Junction Taxi Rank, Durban' },

    // Inanda
    { id: 'kzn_inan_s1', lat: -29.7340, lng: 30.9680, name: 'Inanda — Phoenix Hwy junction', province: 'KZN', type: 'robbery', risk: 0.89, label: 'Road robbery — Phoenix Hwy', street: 'Inanda Rd near Phoenix Hwy junction, Inanda' },

    // Pinetown
    { id: 'kzn_pin_s1', lat: -29.8170, lng: 30.8680, name: 'Old Main Rd Pinetown', province: 'KZN', type: 'carjacking', risk: 0.80, label: 'Carjacking — Old Main Rd', street: 'Old Main Rd, Pinetown CBD' },
    { id: 'kzn_pin_s2', lat: -29.8200, lng: 30.8600, name: 'Pinetown Bus Terminus', province: 'KZN', type: 'robbery', risk: 0.78, label: 'Terminus mugging zone', street: 'King Cetshwayo Hwy / Pinetown Terminus' },

    // ─── EASTERN CAPE ─── Moderate-High (firearms in robberies) ────────────────

    // Motherwell
    { id: 'ec_mth', lat: -33.8167, lng: 25.4167, name: 'Motherwell SAPS Station', province: 'Eastern Cape', type: 'carjacking', risk: 0.87, label: 'SAPS Mod-High — 237 hijackings/quarter', street: 'Motherwell, Gqeberha' },
    { id: 'ec_mth_s1', lat: -33.8211, lng: 25.4082, name: 'Motherwell Shopping Centre', province: 'Eastern Cape', type: 'robbery', risk: 0.86, label: 'Parking lot robbery', street: 'Motherwell Shopping Centre, NU1 Motherwell' },
    { id: 'ec_mth_s2', lat: -33.8150, lng: 25.4220, name: 'Enkwenkwezi Rd & Ngqungqa Rd', province: 'Eastern Cape', type: 'carjacking', risk: 0.84, label: 'Residential carjacking', street: 'Enkwenkwezi Rd & Ngqungqa Rd, Motherwell' },

    // Kwazakele (Gqeberha)
    { id: 'ec_kwa', lat: -33.8333, lng: 25.5833, name: 'Kwazakele SAPS Station', province: 'Eastern Cape', type: 'robbery', risk: 0.83, label: 'SAPS Mod-High — 237 hijackings/quarter', street: 'Kwazakele, Gqeberha' },
    { id: 'ec_kwa_s1', lat: -33.9609, lng: 25.6022, name: 'Pick n Pay Kwazakele Parking', province: 'Eastern Cape', type: 'robbery', risk: 0.82, label: 'Armed robbery — supermarket', street: 'Pick n Pay, Kwazakele, Gqeberha' },

    // Gqeberha Central
    { id: 'ec_gqe_s1', lat: -33.9584, lng: 25.5965, name: 'Govan Mbeki Ave (PE CBD)', province: 'Eastern Cape', type: 'robbery', risk: 0.81, label: 'CBD steet robbery', street: 'Govan Mbeki Ave, Gqeberha CBD' },
    { id: 'ec_gqe_s2', lat: -33.9620, lng: 25.5940, name: 'Gqeberha Station Taxi Rank', province: 'Eastern Cape', type: 'mugging', risk: 0.78, label: 'Commuter area robbery', street: 'Market Square Taxi Rank, Gqeberha' },

    // Mthatha
    { id: 'ec_mta_s1', lat: -31.5886, lng: 28.7836, name: 'Mthatha CBD — Owen St', province: 'Eastern Cape', type: 'robbery', risk: 0.78, label: 'Street robbery — CBD', street: 'Owen St, Mthatha CBD' },
    { id: 'ec_mta_s2', lat: -31.5921, lng: 28.7800, name: 'Mthatha Station Bus Rank', province: 'Eastern Cape', type: 'robbery', risk: 0.76, label: 'Rank area robbery', street: 'Mthatha Bus & Taxi Rank, Nelson Mandela Dr' },

    // East London
    { id: 'ec_eln_s1', lat: -32.9977, lng: 27.9116, name: 'East London — Oxford St', province: 'Eastern Cape', type: 'robbery', risk: 0.80, label: 'CBD robbery zone', street: 'Oxford St, East London CBD' },
    { id: 'ec_eln_s2', lat: -32.9950, lng: 27.9050, name: 'East London Station Forecourt', province: 'Eastern Cape', type: 'mugging', risk: 0.77, label: 'Station approach mugging', street: 'Station Rd, East London' },

    // ─── MPUMALANGA ─── Moderate (truck hijacking N4/N12) ──────────────────────

    { id: 'mp_wit', lat: -25.8701, lng: 29.2340, name: 'Witbank SAPS Station', province: 'Mpumalanga', type: 'hijacking', risk: 0.89, label: 'SAPS Moderate — N4 truck hijacking', street: 'Mandela Dr, eMalahleni (Witbank)' },
    { id: 'mp_wit_s1', lat: -25.8700, lng: 29.2100, name: 'N4 Witbank Weighbridge', province: 'Mpumalanga', type: 'hijacking', risk: 0.91, label: 'N4 truck hijack — weighbridge area', street: 'N4 National Rd, near Witbank Weighbridge' },
    { id: 'mp_wit_s2', lat: -25.8650, lng: 29.2500, name: 'Witbank Mandela Drive (R545)', province: 'Mpumalanga', type: 'carjacking', risk: 0.84, label: 'Carjacking — residential approaches', street: 'Mandela Dr (R545), eMalahleni' },
    { id: 'mp_del_s1', lat: -26.1450, lng: 28.6840, name: 'N12 Delmas — Phola Interchange', province: 'Mpumalanga', type: 'hijacking', risk: 0.88, label: 'N12 hijack zone — Phola interchange', street: 'N12, Delmas near Phola Township off-ramp' },
    { id: 'mp_nel_s1', lat: -25.4743, lng: 30.9699, name: 'Nelspruit — R40 & N4 Merge', province: 'Mpumalanga', type: 'robbery', risk: 0.73, label: 'Armed robbery — R40/N4 merge', street: 'R40 & N4 junction, Nelspruit/Mbombela' },
    { id: 'mp_vos_s1', lat: -26.0920, lng: 28.4270, name: 'Vosman — N12 Corridor', province: 'Mpumalanga', type: 'robbery', risk: 0.72, label: 'Resistance robbery — N12 corridor', street: 'N12 near Vosman, eMalahleni' },

    // ─── NORTH WEST ─── Moderate (mining community robbery) ───────────────────

    { id: 'nw_rus', lat: -25.6545, lng: 27.2422, name: 'Rustenburg SAPS Station', province: 'North West', type: 'carjacking', risk: 0.84, label: 'SAPS Moderate — mining belt hijacking', street: 'Steen St, Rustenburg' },
    { id: 'nw_rus_s1', lat: -25.6540, lng: 27.2490, name: 'Steen St & Brink St Rustenburg', province: 'North West', type: 'robbery', risk: 0.83, label: 'CBD robbery — Rustenburg', street: 'Steen St & Brink St, Rustenburg CBD' },
    { id: 'nw_rus_s2', lat: -25.6480, lng: 27.2380, name: 'Waterfall Mall Approach', province: 'North West', type: 'carjacking', risk: 0.81, label: 'Mall carjacking — morning peak', street: 'Kock St (approach to Waterfall Mall), Rustenburg' },
    { id: 'nw_bri_s1', lat: -25.6275, lng: 27.7840, name: 'Brits — N4 Hartbeespoort Rd', province: 'North West', type: 'carjacking', risk: 0.79, label: 'N4 carjacking corridor — Brits', street: 'N4 near Brits, Hartbeespoort Rd off-ramp' },
    { id: 'nw_pch_s1', lat: -26.7134, lng: 27.0943, name: 'Potchefstroom — Mobara Park', province: 'North West', type: 'robbery', risk: 0.73, label: 'Night robbery — residential fringe', street: 'Leeukuil / Mobara Park, Potchefstroom' },
    { id: 'nw_kle_s1', lat: -26.8710, lng: 26.6720, name: 'Klerksdorp — OR Tambo St', province: 'North West', type: 'robbery', risk: 0.76, label: 'CBD robbery zone', street: 'OR Tambo St, Klerksdorp CBD' },
    { id: 'nw_mma_s1', lat: -25.8571, lng: 25.6415, name: 'Mmabatho Mega City Mall', province: 'North West', type: 'robbery', risk: 0.72, label: 'Large mall robbery', street: 'Mega City Mall, Mmabatho, Mafikeng' },

    // ─── LIMPOPO ─── Low-Moderate (carjacking — SAPS low volume) ───────────────

    { id: 'lp_pol', lat: -23.9045, lng: 29.4685, name: 'Polokwane SAPS Station', province: 'Limpopo', type: 'carjacking', risk: 0.76, label: 'SAPS Low-Moderate — commercial CBD robbery', street: 'Landros Mare St, Polokwane CBD' },
    { id: 'lp_pol_s1', lat: -23.9040, lng: 29.4650, name: 'Polokwane Pick n Pay CBD', province: 'Limpopo', type: 'robbery', risk: 0.75, label: 'Supermarket robbery — armed', street: 'Pick n Pay, Landros Mare St, Polokwane' },
    { id: 'lp_pol_s2', lat: -23.9002, lng: 29.4721, name: 'Polokwane Taxi Rank (Flea Mkt)', province: 'Limpopo', type: 'mugging', risk: 0.73, label: 'Taxi rank mugging zone', street: 'Thabo Mbeki St Taxi Rank, Polokwane' },
    { id: 'lp_pol_s3', lat: -23.9100, lng: 29.4520, name: 'Turfloop Rd (R71) — night risk', province: 'Limpopo', type: 'robbery', risk: 0.70, label: 'Road robbery — after dark', street: 'R71 Turfloop Rd, Polokwane' },
    { id: 'lp_man_s1', lat: -23.8745, lng: 29.6877, name: 'Mankweng — University of Limpopo', province: 'Limpopo', type: 'robbery', risk: 0.72, label: 'Student area robbery', street: 'University Rd, Mankweng near UL campus' },
    { id: 'lp_ses_s1', lat: -23.8814, lng: 29.4541, name: 'Seshego Circle Taxi Rank', province: 'Limpopo', type: 'mugging', risk: 0.74, label: 'Taxi rank robbery', street: 'Seshego Circle, Seshego Township' },
    { id: 'lp_tho_s1', lat: -22.9380, lng: 30.4651, name: 'Thohoyandou — Ha-Mutsha Rd', province: 'Limpopo', type: 'robbery', risk: 0.74, label: 'Cross-border robbery zone', street: 'Ha-Muthsa Rd near Thulamela Mall, Thohoyandou' },
    { id: 'lp_par_s1', lat: -23.9012, lng: 29.4610, name: 'Parkweg — Market Square', province: 'Limpopo', type: 'robbery', risk: 0.65, label: 'Commercial robbery — market', street: 'Market Square, Parkweg, Polokwane' },

    // ─── FREE STATE ─── Low / Commercial robbery ────────────────────────────────

    { id: 'fs_bfn', lat: -29.1214, lng: 26.2149, name: 'Bloemfontein SAPS Station', province: 'Free State', type: 'robbery', risk: 0.74, label: 'SAPS Low — commercial robbery in CBD', street: 'Maitland St, Bloemfontein CBD' },
    { id: 'fs_bfn_s1', lat: -29.1195, lng: 26.2121, name: 'Bloemfontein Station Sq', province: 'Free State', type: 'robbery', risk: 0.74, label: 'Station square robbery', street: 'Station Square, Maitland St, Bloemfontein' },
    { id: 'fs_bfn_s2', lat: -29.1177, lng: 26.2180, name: 'Mimosa Mall Parking Lot', province: 'Free State', type: 'carjacking', risk: 0.72, label: 'Mall parking carjacking', street: 'Mimosa Mall, N1 Parfitt Ave Bloemfontein' },
    { id: 'fs_tha_s1', lat: -27.9870, lng: 26.7082, name: 'Thabong — Welkom CBD', province: 'Free State', type: 'robbery', risk: 0.80, label: 'High robbery — Welkom CBD', street: 'Stateway, Welkom CBD near Thabong' },
    { id: 'fs_tha_s2', lat: -27.9790, lng: 26.7200, name: 'Welkom Shopping — Taung St', province: 'Free State', type: 'robbery', risk: 0.78, label: 'Armed robbery — Shoprite', street: 'Shoprite Welkom, Taung St, Welkom' },
    { id: 'fs_zam_s1', lat: -26.9000, lng: 27.8278, name: 'Zamdela — Vaal Rd crossing', province: 'Free State', type: 'robbery', risk: 0.79, label: 'Robbery near Vaal industrial corridor', street: 'Vaal Rd crossing, Zamdela, Sasolburg area' },
    { id: 'fs_bls_s1', lat: -29.0878, lng: 26.1622, name: 'Bloemspruit — R706 intercept', province: 'Free State', type: 'carjacking', risk: 0.71, label: 'Carjacking — highway intercept', street: 'R706 near Bloemspruit, Bloemfontein South' },
    { id: 'fs_wes_s1', lat: -23.9140, lng: 29.4410, name: 'Westernburg — Seshego Rd', province: 'Limpopo', type: 'robbery', risk: 0.67, label: 'Commercial robbery', street: 'Seshego Rd, Westernburg, Polokwane' },

    // ─── NORTHERN CAPE ─── Lowest (common robbery) ─────────────────────────────

    { id: 'nc_gal', lat: -28.7457, lng: 24.7629, name: 'Galeshewe SAPS Station', province: 'Northern Cape', type: 'robbery', risk: 0.77, label: 'SAPS Lowest — common robbery', street: 'Freedom Dr, Galeshewe, Kimberley' },
    { id: 'nc_gal_s1', lat: -28.7420, lng: 24.7590, name: 'Freedom Dr & Pampierstad Rd', province: 'Northern Cape', type: 'robbery', risk: 0.76, label: 'Street robbery — Galeshewe', street: 'Freedom Dr & Pampierstad Rd, Galeshewe' },
    { id: 'nc_kim_s1', lat: -28.7383, lng: 24.7705, name: 'Kimberley CBD — Du Toitspan Rd', province: 'Northern Cape', type: 'robbery', risk: 0.73, label: 'CBD robbery zone', street: 'Du Toitspan Rd, Kimberley CBD' },
    { id: 'nc_kim_s2', lat: -28.7450, lng: 24.7820, name: 'Diamond Mall Kimberley', province: 'Northern Cape', type: 'robbery', risk: 0.70, label: 'Mall robbery — parking', street: 'Diamond Pavilion Mall, Bultfontein Rd, Kimberley' },
    { id: 'nc_upt_s1', lat: -28.4478, lng: 21.2561, name: 'Upington — Scott St Commercial', province: 'Northern Cape', type: 'robbery', risk: 0.68, label: 'Commercial robbery — road travellers', street: 'Scott St, Upington CBD' },
    { id: 'nc_rod_s1', lat: -28.7300, lng: 24.7950, name: 'Roodepan — Havenga St', province: 'Northern Cape', type: 'robbery', risk: 0.65, label: 'Common robbery — residential', street: 'Havenga St, Roodepan, Kimberley' },
];

// =============================================================================
// UTILITIES
// =============================================================================
function riskToColor(risk) {
    if (risk >= 0.75) return '#e41e26';
    if (risk >= 0.50) return '#ff7600';
    if (risk >= 0.30) return '#ffc300';
    return '#00cc66';
}
function riskLabel(risk) {
    if (risk >= 0.85) return 'EXTREME RISK';
    if (risk >= 0.70) return 'HIGH RISK';
    if (risk >= 0.50) return 'MODERATE RISK';
    if (risk >= 0.30) return 'LOW-MODERATE';
    return 'SAFE';
}
function haversineKm(lat1, lng1, lat2, lng2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}
// eslint-disable-next-line no-unused-vars
function bearing(lat1, lng1, lat2, lng2) {
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const y = Math.sin(dLng) * Math.cos(lat2 * Math.PI / 180);
    const x = Math.cos(lat1 * Math.PI / 180) * Math.sin(lat2 * Math.PI / 180) - Math.sin(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.cos(dLng);
    return ((Math.atan2(y, x) * 180 / Math.PI) + 360) % 360;
}
function formatDist(meters) {
    if (meters >= 1000) return `${(meters / 1000).toFixed(1)} km`;
    return `${Math.round(meters)} m`;
}
function formatDuration(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (h > 0) return `${h}h ${m}m`;
    return `${m} min`;
}

// Maneuver → label/icon mapping (OSRM types)
const MANEUVER_ICONS = {
    'turn-left': { icon: '↰', label: 'Turn left' },
    'turn-right': { icon: '↱', label: 'Turn right' },
    'turn-sharp-left': { icon: '⬅', label: 'Sharp left' },
    'turn-sharp-right': { icon: '➡', label: 'Sharp right' },
    'turn-slight-left': { icon: '↖', label: 'Slight left' },
    'turn-slight-right': { icon: '↗', label: 'Slight right' },
    'continue': { icon: '⬆', label: 'Continue' },
    'roundabout': { icon: '🔄', label: 'Roundabout' },
    'merge': { icon: '⬆', label: 'Merge' },
    'ramp': { icon: '↗', label: 'Take ramp' },
    'depart': { icon: '🚦', label: 'Start' },
    'arrive': { icon: '🏁', label: 'Arrive' },
    'default': { icon: '⬆', label: 'Continue' },
};

function getManeuverInfo(step) {
    if (!step || !step.maneuver) return MANEUVER_ICONS['default'];
    const type = step.maneuver.type || '';
    const mod = step.maneuver.modifier || '';
    const key = mod ? `${type}-${mod}` : type;
    return MANEUVER_ICONS[key] || MANEUVER_ICONS[type] || MANEUVER_ICONS['default'];
}

// =============================================================================
// CUSTOM ICONS
// =============================================================================
function createHotspotIcon(risk) {
    const color = riskToColor(risk);
    const size = risk >= 0.75 ? 16 : risk >= 0.50 ? 13 : 11;
    return L.divIcon({
        className: '',
        html: `<div style="background:${color};width:${size}px;height:${size}px;border-radius:50%;border:2px solid rgba(255,255,255,0.8);box-shadow:0 0 ${size}px ${color}88;"></div>`,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
    });
}
function createUserIcon(heading) {
    return L.divIcon({
        className: '',
        html: `<div class="sr-user-icon" style="transform:rotate(${heading || 0}deg)"><div class="sr-user-arrow"></div><div class="sr-user-dot"></div><div class="sr-user-ring"></div></div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
    });
}
function createDestIcon() {
    return L.divIcon({
        className: '',
        html: `<div class="sr-dest-icon"><span style="font-size:26px;" role="img">&#x1F3C1;</span><div class="sr-dest-pulse"></div></div>`,
        iconSize: [32, 48],
        iconAnchor: [16, 48],
    });
}

// =============================================================================
// MAP FOLLOWER — re-centers map on user while navigating
// =============================================================================
function MapFollower({ userPos, isNavigating, destination, routeCoords }) {
    const map = useMap();
    const navRef = useRef(false);

    useEffect(() => {
        if (isNavigating && userPos) {
            map.setView([userPos.lat, userPos.lng], 17, { animate: true, duration: 0.8 });
            navRef.current = true;
        }
    }, [userPos, isNavigating, map]);

    useEffect(() => {
        if (!isNavigating && navRef.current) {
            // Exited navigation — fit route bounds
            if (routeCoords && routeCoords.length >= 2) {
                const bounds = L.latLngBounds(routeCoords.map(p => [p.lat, p.lng]));
                map.fitBounds(bounds, { padding: [40, 40] });
            }
            navRef.current = false;
        } else if (!isNavigating && destination) {
            map.flyTo([destination.lat, destination.lng], 13, { duration: 1.5 });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isNavigating]);

    return null;
}

// =============================================================================
// HEATMAP LAYER
// =============================================================================
function HeatmapLayer({ points }) {
    const map = useMap();
    const heatRef = useRef(null);

    useEffect(() => {
        const applyHeat = () => {
            if (!window.L || !window.L.heatLayer) return;
            if (heatRef.current) map.removeLayer(heatRef.current);
            const data = points.map(p => [p.lat, p.lng, p.risk]);
            heatRef.current = window.L.heatLayer(data, {
                radius: 35, blur: 25, maxZoom: 14, max: 1.0,
                gradient: { 0.0: 'rgba(0,200,100,0)', 0.3: 'rgba(0,200,100,0.5)', 0.5: 'rgba(255,195,0,0.7)', 0.7: 'rgba(255,118,0,0.8)', 0.85: 'rgba(228,30,38,0.9)', 1.0: 'rgba(180,0,0,1)' },
            }).addTo(map);
        };
        if (window.L && window.L.heatLayer) {
            applyHeat();
        } else {
            const existing = document.querySelector('script[data-leaflet-heat]');
            if (!existing) {
                const s = document.createElement('script');
                s.src = 'https://cdn.jsdelivr.net/npm/leaflet.heat@0.2.0/dist/leaflet-heat.js';
                s.setAttribute('data-leaflet-heat', '1');
                s.onload = applyHeat;
                document.head.appendChild(s);
            } else {
                setTimeout(applyHeat, 800);
            }
        }
        return () => { if (heatRef.current) map.removeLayer(heatRef.current); };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [points]);

    return null;
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================
const SafeRouteMapComponent = ({
    onMapReady = null,
    onMarkerClick = null,
    onHazardDetected = null,
    route = null,
    userLocation = null,
    onRouteCalculated = null,
    isActiveNavigation = null,
}) => {
    const navigate = useNavigate();
    const mapRef = useRef(null);

    // ── Core state ─────────────────────────────────────────────────────────────
    const [backendHotspots, setBackendHotspots] = useState([]);
    const [backendHazardZones, setBackendHazardZones] = useState([]);
    const [showHeatmap, setShowHeatmap] = useState(true);
    const [showHotspots, setShowHotspots] = useState(true);
    const [showHazardZones, setShowHazardZones] = useState(true);
    const [mapError, setMapError] = useState(null);

    // ── Search / Autocomplete ───────────────────────────────────────────────────
    const [destinationQuery, setDestinationQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [isSearching, setIsSearching] = useState(false);
    const [searchError, setSearchError] = useState('');
    const autocompleteTimer = useRef(null);

    // ── Route state ─────────────────────────────────────────────────────────────
    const [destination, setDestination] = useState(null);
    const [routeSegments, setRouteSegments] = useState([]);
    const [routeSteps, setRouteSteps] = useState([]);   // OSRM steps
    const [fullRouteCoords, setFullRouteCoords] = useState([]);
    const [routeInfo, setRouteInfo] = useState(null);
    const [routeMode, setRouteMode] = useState('safest');
    const [isCalculatingRoute, setIsCalculatingRoute] = useState(false);

    // ── Navigation state ────────────────────────────────────────────────────────
    const [isNavigating, setIsNavigating] = useState(false);
    const [currentStepIdx, setCurrentStepIdx] = useState(0);
    const [distanceRemaining, setDistanceRemaining] = useState(null);
    const [timeRemaining, setTimeRemaining] = useState(null);
    const [userHeading, setUserHeading] = useState(0);
    const watchIdRef = useRef(null);
    const [isRerouting, setIsRerouting] = useState(false);
    const [rerouteToast, setRerouteToast] = useState('');

    // ── Simulation state ────────────────────────────────────────────────────────
    const [isSimulating, setIsSimulating] = useState(localStorage.getItem('sr_sim_active') === 'true');
    const [simPos, setSimPos] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('sr_sim_pos') || 'null');
        } catch (e) {
            return null;
        }
    });
    const [simCoordIdx, setSimCoordIdx] = useState(() => {
        return parseInt(localStorage.getItem('sr_sim_coord_idx') || '0', 10);
    });
    const lastUpdateRef = useRef(Date.now());

    // ── Live GPS position (from parent or watchPosition) ───────────────────────
    const [livePos, setLivePos] = useState(null);

    // ── Incident alert ──────────────────────────────────────────────────────────
    const [incidentAlert, setIncidentAlert] = useState(null);
    const [backendConnected, setBackendConnected] = useState(false);
    const incidentPollRef = useRef(null);
    const knownIncidentIds = useRef(new Set());

    // Normalise userLocation format
    const parentUserPos = userLocation
        ? { lat: userLocation.latitude ?? userLocation.lat, lng: userLocation.longitude ?? userLocation.lng }
        : null;

    const userPos = isSimulating ? simPos : (livePos || parentUserPos);

    const defaultCenter = [-26.2041, 28.0473]; // JHB
    const mapCenter = userPos ? [userPos.lat, userPos.lng] : defaultCenter;
    const allHotspots = [...SA_CRIME_HOTSPOTS, ...backendHotspots];

    // ── Score risk for a coordinate against known hotspots ─────────────────────
    const scoreRisk = useCallback((lat, lng) => {
        return allHotspots.reduce((mx, h) => {
            const d = haversineKm(lat, lng, h.lat, h.lng);
            return d < 1.5 ? Math.max(mx, h.risk * (1 - d / 1.5)) : mx;
        }, 0.12);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [allHotspots.length]);

    // ── Persist navigation state for AR HUD ─────────────────────────────────────
    useEffect(() => {
        if (isNavigating) {
            localStorage.setItem('sr_nav_active', 'true');
            localStorage.setItem('sr_nav_steps', JSON.stringify(routeSteps));
            localStorage.setItem('sr_nav_step_idx', currentStepIdx.toString());
            localStorage.setItem('sr_nav_info', JSON.stringify(routeInfo));
            localStorage.setItem('sr_nav_dest', destinationQuery);
            if (destination) {
                localStorage.setItem('sr_nav_dest_obj', JSON.stringify(destination));
            }
            if (routeSegments.length > 0) {
                localStorage.setItem('sr_nav_segments', JSON.stringify(routeSegments));
                localStorage.setItem('sr_nav_full_coords', JSON.stringify(fullRouteCoords));
            }
        } else {
            localStorage.removeItem('sr_nav_active');
            localStorage.removeItem('sr_nav_steps');
            localStorage.removeItem('sr_nav_step_idx');
            localStorage.removeItem('sr_nav_info');
            localStorage.removeItem('sr_nav_dest');
            localStorage.removeItem('sr_nav_dest_obj');
            localStorage.removeItem('sr_nav_segments');
            localStorage.removeItem('sr_nav_full_coords');
        }
    }, [isNavigating, routeSteps, currentStepIdx, routeInfo, destinationQuery, destination, routeSegments, fullRouteCoords]);

    // ── Simulation logic ────────────────────────────────────────────────────────
    useEffect(() => {
        if (!isNavigating || !isSimulating) return;

        const simInterval = setInterval(() => {
            moveSimulatedUser();
        }, 2000);

        return () => clearInterval(simInterval);
    }, [isNavigating, isSimulating, fullRouteCoords, currentStepIdx, simPos, simCoordIdx]);

    const moveSimulatedUser = () => {
        if (!fullRouteCoords.length) return;

        const now = Date.now();
        const dt = (now - lastUpdateRef.current) / 1000;
        lastUpdateRef.current = now;

        const speed = 0.0111; // 40km/h
        let distanceToMove = speed * dt;

        let curIdx = simCoordIdx;
        let pos = simPos;

        if (!pos && fullRouteCoords[curIdx]) {
            pos = { lat: fullRouteCoords[curIdx][0], lng: fullRouteCoords[curIdx][1] };
        }

        while (distanceToMove > 0 && curIdx < fullRouteCoords.length - 1) {
            const nextCoord = fullRouteCoords[curIdx + 1];
            const dist = haversineKm(pos.lat, pos.lng, nextCoord[0], nextCoord[1]);

            if (distanceToMove >= dist) {
                distanceToMove -= dist;
                curIdx++;
                pos = { lat: nextCoord[0], lng: nextCoord[1] };
            } else {
                const ratio = distanceToMove / dist;
                pos = {
                    lat: pos.lat + (nextCoord[0] - pos.lat) * ratio,
                    lng: pos.lng + (nextCoord[1] - pos.lng) * ratio
                };
                distanceToMove = 0;
            }
        }

        setSimPos(pos);
        setSimCoordIdx(curIdx);
        localStorage.setItem('sr_sim_pos', JSON.stringify(pos));
        localStorage.setItem('sr_sim_coord_idx', curIdx.toString());

        // Auto-advance step if close
        if (currentIdx < routeSteps.length - 1) {
            const nextStep = routeSteps[currentIdx + 1];
            const [nLng, nLat] = nextStep.maneuver.location;
            if (haversineKm(pos.lat, pos.lng, nLat, nLng) < 0.05) {
                setCurrentStepIdx(v => v + 1);
                localStorage.setItem('sr_nav_step_idx', (currentIdx + 1).toString());
            }
        }
    };

    const toggleSimulation = () => {
        const newState = !isSimulating;
        setIsSimulating(newState);
        localStorage.setItem('sr_sim_active', newState ? 'true' : 'false');
        lastUpdateRef.current = Date.now();
        
        if (newState) {
            // Find coordinate closest to current maneuver or start
            let startPos;
            let startIdx = 0;

            if (routeSteps[currentStepIdx]) {
                const [lng, lat] = routeSteps[currentStepIdx].maneuver.location;
                startPos = { lat, lng };
                
                // Find closest index in fullRouteCoords
                let minDist = Infinity;
                fullRouteCoords.forEach((c, i) => {
                    const d = haversineKm(lat, lng, c[0], c[1]);
                    if (d < minDist) {
                        minDist = d;
                        startIdx = i;
                    }
                });
            } else if (fullRouteCoords.length > 0) {
                startPos = { lat: fullRouteCoords[0][0], lng: fullRouteCoords[0][1] };
            }

            if (startPos) {
                setSimPos(startPos);
                setSimCoordIdx(startIdx);
                localStorage.setItem('sr_sim_pos', JSON.stringify(startPos));
                localStorage.setItem('sr_sim_coord_idx', startIdx.toString());
            }
        }
    };

    // Listen for storage changes from HUD
    useEffect(() => {
        const handleStorage = (e) => {
            if (e.key === 'sr_sim_active') setIsSimulating(e.newValue === 'true');
            if (e.key === 'sr_sim_pos' && e.newValue) {
                try { setSimPos(JSON.parse(e.newValue)); } catch (_) {}
            }
            if (e.key === 'sr_sim_coord_idx' && e.newValue) {
                setSimCoordIdx(parseInt(e.newValue, 10));
            }
            if (e.key === 'sr_nav_step_idx' && e.newValue) {
                setCurrentStepIdx(parseInt(e.newValue, 10));
            }
        };
        window.addEventListener('storage', handleStorage);
        return () => window.removeEventListener('storage', handleStorage);
    }, []);

    // ── Restore navigation state on mount ───────────────────────────────────────
    useEffect(() => {
        const isNavActive = localStorage.getItem('sr_nav_active') === 'true';
        if (isNavActive && !isNavigating) {
            try {
                const savedSteps = JSON.parse(localStorage.getItem('sr_nav_steps') || 'null');
                const savedIdx = parseInt(localStorage.getItem('sr_nav_step_idx') || '0', 10);
                const savedInfo = JSON.parse(localStorage.getItem('sr_nav_info') || 'null');
                const savedDestQ = localStorage.getItem('sr_nav_dest') || '';
                const savedDestObj = JSON.parse(localStorage.getItem('sr_nav_dest_obj') || 'null');
                const savedSegs = JSON.parse(localStorage.getItem('sr_nav_segments') || 'null');
                const savedCoords = JSON.parse(localStorage.getItem('sr_nav_full_coords') || 'null');

                if (savedSteps && savedSteps.length > 0 && savedInfo) {
                    setIsNavigating(true);
                    setRouteSteps(savedSteps);
                    setCurrentStepIdx(savedIdx);
                    setRouteInfo(savedInfo);
                    setDestinationQuery(savedDestQ);
                    if (savedDestObj) setDestination(savedDestObj);
                    if (savedSegs) setRouteSegments(savedSegs);
                    if (savedCoords) setFullRouteCoords(savedCoords);
                    startGPSWatch();
                }
            } catch (e) {
                console.error("Failed to restore map state", e);
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // ── Fetch live data from backend ────────────────────────────────────────────
    useEffect(() => {
        const fetchLive = async () => {
            try {
                const [markersRes, hazardRes] = await Promise.all([
                    apiService.getMapMarkers(),
                    apiService.getHazardZones(),
                ]);
                if (markersRes.success && markersRes.markers) {
                    setBackendHotspots(markersRes.markers.map((m, i) => ({
                        id: `be_${i}`, lat: m.position.lat, lng: m.position.lng,
                        name: m.title, province: 'Edge-AI Detected', type: m.type || 'incident',
                        risk: m.severity, label: m.description,
                    })));
                }
                if (hazardRes.success && hazardRes.hazard_zones) setBackendHazardZones(hazardRes.hazard_zones);
                setBackendConnected(true);
            } catch (_) { setBackendConnected(false); }
        };
        fetchLive();
        const iv = setInterval(fetchLive, 60000);
        return () => clearInterval(iv);
    }, []);

    // ── Incident polling during navigation ──────────────────────────────────────
    useEffect(() => {
        if (!isNavigating) {
            if (incidentPollRef.current) clearInterval(incidentPollRef.current);
            return;
        }
        const checkIncidents = async () => {
            try {
                const res = await apiService.getMapMarkers();
                if (!res.success || !res.markers) return;
                for (const m of res.markers) {
                    const id = `${m.position.lat}_${m.position.lng}_${m.type}`;
                    if (knownIncidentIds.current.has(id)) continue;
                    // Check proximity to remaining route
                    if (fullRouteCoords.length > currentStepIdx * 2) {
                        const remaining = fullRouteCoords.slice(currentStepIdx * 2);
                        const nearby = remaining.some(([lat, lng]) => haversineKm(lat, lng, m.position.lat, m.position.lng) < 2.0);
                        if (nearby) {
                            knownIncidentIds.current.add(id);
                            setIncidentAlert({ type: m.type, title: m.title, severity: m.severity, position: m.position });
                            // Auto-reroute if extreme
                            if (m.severity >= 0.85 && userPos) {
                                handleReroute(userPos, { autoReason: m.title });
                            }
                        }
                    }
                }
            } catch (_) { }
        };
        incidentPollRef.current = setInterval(checkIncidents, 30000);
        return () => clearInterval(incidentPollRef.current);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isNavigating, fullRouteCoords, currentStepIdx, userPos]);

    // ── GPS watchPosition ───────────────────────────────────────────────────────
    const startGPSWatch = useCallback(() => {
        if (!navigator.geolocation) return;
        watchIdRef.current = navigator.geolocation.watchPosition(
            (pos) => {
                const p = { lat: pos.coords.latitude, lng: pos.coords.longitude };
                setLivePos(p);
                if (pos.coords.heading) setUserHeading(pos.coords.heading);

                // Auto-advance steps
                if (routeSteps.length > 0 && currentStepIdx < routeSteps.length - 1) {
                    const nextStep = routeSteps[currentStepIdx + 1];
                    if (nextStep && nextStep.maneuver && nextStep.maneuver.location) {
                        const [sLng, sLat] = nextStep.maneuver.location;
                        const dist = haversineKm(p.lat, p.lng, sLat, sLng);
                        if (dist < 0.05) setCurrentStepIdx(idx => idx + 1);
                    }
                }

                // Update remaining distance
                if (destination) {
                    const rem = haversineKm(p.lat, p.lng, destination.lat, destination.lng);
                    setDistanceRemaining((rem * 1000).toFixed(0));
                    setTimeRemaining(Math.round(rem / 0.6));
                }
            },
            () => { },
            { enableHighAccuracy: true, maximumAge: 2000, timeout: 10000 }
        );
    }, [routeSteps, currentStepIdx, destination]);

    const stopGPSWatch = useCallback(() => {
        if (watchIdRef.current !== null) {
            navigator.geolocation.clearWatch(watchIdRef.current);
            watchIdRef.current = null;
        }
    }, []);

    // ── Autocomplete (Nominatim) ────────────────────────────────────────────────
    const fetchSuggestions = useCallback(async (q) => {
        if (!q || q.length < 3) { setSuggestions([]); return; }
        try {
            // Clean query to avoid double "South Africa"
            let cleanQ = q.replace(/,\s*South Africa/gi, '').trim();
            const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(cleanQ + ', South Africa')}&limit=8&countrycodes=za&addressdetails=1`;

            // Simple GET request without custom headers to avoid CORS preflight issues
            const res = await fetch(url);
            const data = await res.json();
            setSuggestions(data.map(d => ({
                id: d.place_id,
                display: d.display_name,
                short: [d.address?.road, d.address?.suburb, d.address?.city || d.address?.town || d.address?.village].filter(Boolean).join(', '),
                lat: parseFloat(d.lat),
                lng: parseFloat(d.lon),
            })));
            setShowSuggestions(true);
        } catch (_) { setSuggestions([]); }
    }, []);

    const handleQueryChange = (e) => {
        const v = e.target.value;
        setDestinationQuery(v);
        setSearchError('');
        clearTimeout(autocompleteTimer.current);
        autocompleteTimer.current = setTimeout(() => fetchSuggestions(v), 350);
    };

    const selectSuggestion = (s) => {
        setDestinationQuery(s.display);
        setShowSuggestions(false);
        setSuggestions([]);
        setDestination({ lat: s.lat, lng: s.lng, display: s.display });
        triggerRouteCalc({ lat: s.lat, lng: s.lng });
    };

    // ── OSRM routing ────────────────────────────────────────────────────────────
    const fetchOSRMRoute = async (start, end) => {
        const url = `https://router.project-osrm.org/route/v1/driving/${start.lng},${start.lat};${end.lng},${end.lat}?steps=true&geometries=geojson&overview=full`;
        const res = await fetch(url);
        if (!res.ok) throw new Error('Routing unavailable');
        const data = await res.json();
        if (!data.routes || data.routes.length === 0) throw new Error('No route found');
        return data.routes[0];
    };

    const triggerRouteCalc = async (dest, startOverride) => {
        const start = startOverride || userPos || parentUserPos;
        if (!start) { setSearchError('Enable location to calculate routes'); return; }
        setIsCalculatingRoute(true);
        setRouteSegments([]);
        setRouteSteps([]);
        setFullRouteCoords([]);
        setRouteInfo(null);
        setCurrentStepIdx(0);

        try {
            // 1 — Try OSRM for real road routing
            const osrmRoute = await fetchOSRMRoute(start, dest);
            const coords = osrmRoute.geometry.coordinates.map(([lng, lat]) => [lat, lng]);
            setFullRouteCoords(coords);

            // 2 — Score each coord pair by crime proximity
            const segs = [];
            for (let i = 0; i < coords.length - 1; i++) {
                const risk = scoreRisk(coords[i][0], coords[i][1]);
                segs.push({ coords: [coords[i], coords[i + 1]], risk, color: riskToColor(risk) });
            }
            setRouteSegments(segs);

            // 3 — Extract turn steps
            const steps = osrmRoute.legs.flatMap(leg => leg.steps);
            setRouteSteps(steps);

            // 4 — Route summary
            const totalRisk = segs.reduce((s, x) => s + x.risk, 0) / segs.length;
            const info = {
                distance: formatDist(osrmRoute.distance),
                duration: formatDuration(osrmRoute.duration),
                safetyScore: Math.round((1 - totalRisk) * 100),
            };
            setRouteInfo(info);
            setDistanceRemaining(osrmRoute.distance);
            setTimeRemaining(osrmRoute.duration / 60);
            if (onRouteCalculated) onRouteCalculated({ distance: osrmRoute.distance, duration: osrmRoute.duration, safetyScore: info.safetyScore });

        } catch (_) {
            // Fallback — straight line with hotspot risk scoring
            buildFallbackRoute(start, dest);
        } finally {
            setIsCalculatingRoute(false);
        }
    };

    const buildFallbackRoute = (start, dest) => {
        const steps = 12;
        const coords = [];
        for (let i = 0; i <= steps; i++) {
            const t = i / steps;
            const jitter = () => (Math.random() - 0.5) * 0.003;
            coords.push([start.lat + (dest.lat - start.lat) * t + jitter(), start.lng + (dest.lng - start.lng) * t + jitter()]);
        }
        setFullRouteCoords(coords);
        const segs = [];
        for (let i = 0; i < coords.length - 1; i++) {
            const risk = scoreRisk(coords[i][0], coords[i][1]);
            segs.push({ coords: [coords[i], coords[i + 1]], risk, color: riskToColor(risk) });
        }
        setRouteSegments(segs);
        const distKm = haversineKm(start.lat, start.lng, dest.lat, dest.lng);
        setRouteInfo({ distance: `${distKm.toFixed(1)} km`, duration: `${Math.round(distKm * 2)} min`, safetyScore: 74 });
        setRouteSteps([{ maneuver: { type: 'depart' }, name: 'Proceed to destination', distance: distKm * 1000 }]);
        setDistanceRemaining((distKm * 1000).toFixed(0));
        setTimeRemaining(Math.round(distKm * 2));
    };

    // ── Search form submit ──────────────────────────────────────────────────────
    const handleSearch = async (e) => {
        if (e) e.preventDefault();
        const rawQ = destinationQuery.trim();
        if (!rawQ) return;
        setIsSearching(true);
        setShowSuggestions(false);
        setSearchError('');

        const performFetch = async (queryText) => {
            let cleanQ = queryText.replace(/,\s*South Africa/gi, '').trim();
            const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(cleanQ + ', South Africa')}&limit=1&countrycodes=za`;
            const res = await fetch(url);
            return await res.json();
        };

        try {
            // Attempt 1: Full query (house number + street)
            let data = await performFetch(rawQ);

            // Attempt 2: Fallback — Strip house number if no result found
            // Matches leading "43 " or similar number patterns
            if (!data.length && /^\d+\s+/.test(rawQ)) {
                const fallbackQ = rawQ.replace(/^\d+\s+/, '');
                data = await performFetch(fallbackQ);
                if (data.length) setSearchError(`House number not found. Showing ${fallbackQ} instead.`);
            }

            if (!data.length) throw new Error(`"${rawQ}" not found. Try a street name or different spelling.`);

            const dest = { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon), display: data[0].display_name };
            setDestination(dest);
            setDestinationQuery(dest.display);
            await triggerRouteCalc(dest);
        } catch (err) {
            setSearchError(err.message || 'Search failed. Please try again.');
        } finally {
            setIsSearching(false);
        }
    };

    // ── Start Navigation ────────────────────────────────────────────────────────
    const handleStartNavigation = () => {
        setIsNavigating(true);
        setCurrentStepIdx(0);
        setIncidentAlert(null);
        knownIncidentIds.current.clear();
        startGPSWatch();
        // Request a fresh GPS position immediately
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(pos => {
                setLivePos({ lat: pos.coords.latitude, lng: pos.coords.longitude });
            });
        }
    };

    // ── End Navigation ──────────────────────────────────────────────────────────
    const handleEndNavigation = () => {
        setIsNavigating(false);
        stopGPSWatch();
        setIncidentAlert(null);
        localStorage.removeItem('sr_nav_active');
    };

    // ── Switch to AR HUD ────────────────────────────────────────────────────────
    const handleSwitchToAR = () => {
        navigate('/hazard-hud');
    };

    // ── Manual Reroute ──────────────────────────────────────────────────────────
    const handleReroute = async (fromPos, opts = {}) => {
        if (!destination || isRerouting) return;
        setIsRerouting(true);
        setIncidentAlert(null);
        const reason = opts.autoReason ? `Auto-rerouted: ${opts.autoReason}` : 'Rerouting to avoid hazard...';
        setRerouteToast(reason);
        try {
            await triggerRouteCalc(destination, fromPos || userPos);
        } finally {
            setIsRerouting(false);
            setTimeout(() => setRerouteToast(''), 3000);
        }
    };

    // ── Route prop from parent ──────────────────────────────────────────────────
    useEffect(() => {
        if (route && route.segments) {
            const parsed = route.segments.map(seg => ({
                coords: [
                    [seg.start_point?.lat ?? seg.start_lat, seg.start_point?.lng ?? seg.start_lng],
                    [seg.end_point?.lat ?? seg.end_lat, seg.end_point?.lng ?? seg.end_lng],
                ],
                risk: seg.risk_score,
                color: riskToColor(seg.risk_score),
            }));
            setRouteSegments(parsed);

            // Restore the destination marker from the final segment
            if (parsed.length > 0 && !destination) {
                const finalSegment = parsed[parsed.length - 1];
                const endLat = finalSegment.coords[1][0];
                const endLng = finalSegment.coords[1][1];
                setDestination({ lat: endLat, lng: endLng, display: 'Destination' });
            }
        }
    }, [route, destination]);

    useEffect(() => {
        if (isActiveNavigation === true) {
            setIsNavigating(true);
        } else if (isActiveNavigation === false) {
            setIsNavigating(false);
        }
    }, [isActiveNavigation]);

    // ── Map ready callback ──────────────────────────────────────────────────────
    const handleMapReady = useCallback((map) => {
        mapRef.current = map;
        if (onMapReady) onMapReady(map);
    }, [onMapReady]);

    const routeCoords = fullRouteCoords.length > 0
        ? fullRouteCoords.map(([lat, lng]) => ({ lat, lng }))
        : routeSegments.flatMap(s => s.coords.map(([lat, lng]) => ({ lat, lng })));

    const heatmapPoints = allHotspots.map(h => ({ lat: h.lat, lng: h.lng, risk: h.risk }));
    const currentStep = routeSteps[currentStepIdx] || null;
    const maneuver = getManeuverInfo(currentStep);

    if (mapError) {
        return (
            <div className="sr-map-error">
                <div className="sr-map-error-icon">🗺️</div>
                <h3>Map Error</h3><p>{mapError}</p>
                <button onClick={() => setMapError(null)}>Retry</button>
            </div>
        );
    }

    return (
        <div className={`sr-map-wrapper ${isNavigating ? 'sr-nav-active' : ''}`}>

            {/* ══ NAVIGATION HUD (top) — turn-by-turn ══════════════════════════════ */}
            {isNavigating && currentStep && (
                <div className="sr-nav-hud-top">
                    <div className="sr-nav-maneuver-icon">{maneuver.icon}</div>
                    <div className="sr-nav-turn-info">
                        <div className="sr-nav-maneuver-label">{maneuver.label}{currentStep.name ? ` onto ${currentStep.name}` : ''}</div>
                        <div className="sr-nav-step-dist">
                            {currentStepIdx < routeSteps.length - 1
                                ? `in ${formatDist(currentStep.distance || 0)}`
                                : 'You have arrived'}
                        </div>
                    </div>
                    <div className="sr-nav-hud-actions">
                        <button className={`sr-sim-toggle-btn ${isSimulating ? 'active' : ''}`} onClick={toggleSimulation} title="Toggle Demo Simulation">
                            {isSimulating ? '⏹️' : '🚀'}
                        </button>
                        <button className="sr-ar-toggle-btn" onClick={handleSwitchToAR} title="Switch to AR Camera HUD">
                            📷 <span>AR HUD</span>
                        </button>
                        <div className="sr-nav-step-count">{currentStepIdx + 1}/{routeSteps.length}</div>
                    </div>
                </div>
            )}

            {/* ══ INCIDENT ALERT BANNER ═════════════════════════════════════════════ */}
            {incidentAlert && (
                <div className="sr-incident-alert">
                    <div className="sr-incident-icon">⚠️</div>
                    <div className="sr-incident-body">
                        <div className="sr-incident-title">{incidentAlert.type?.toUpperCase()} AHEAD</div>
                        <div className="sr-incident-sub">{incidentAlert.title}</div>
                    </div>
                    <div className="sr-incident-actions">
                        <button className="sr-reroute-btn" onClick={() => handleReroute(userPos)}>Reroute</button>
                        <button className="sr-dismiss-btn" onClick={() => setIncidentAlert(null)}>Dismiss</button>
                    </div>
                </div>
            )}

            {/* ══ REROUTING TOAST ══════════════════════════════════════════════════ */}
            {(rerouteToast || isRerouting) && (
                <div className="sr-reroute-toast">
                    {isRerouting ? <span className="sr-spinner" /> : '🔄'} {rerouteToast || 'Recalculating...'}
                </div>
            )}

            {/* ══ SEARCH BAR (hidden during navigation) ════════════════════════════ */}
            {!isNavigating && (
                <div className="sr-search-bar">
                    <form onSubmit={handleSearch} className="sr-search-form">
                        <span className="sr-search-icon">🔍</span>
                        <input
                            type="text"
                            placeholder="14 Long Street, Cape Town or any SA address..."
                            value={destinationQuery}
                            onChange={handleQueryChange}
                            onFocus={() => suggestions.length && setShowSuggestions(true)}
                            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                            className="sr-search-input"
                            autoComplete="off"
                        />
                        {destinationQuery && (
                            <button type="button" className="sr-search-clear"
                                onClick={() => { setDestinationQuery(''); setDestination(null); setRouteSegments([]); setRouteInfo(null); setSearchError(''); setSuggestions([]); }}>×</button>
                        )}
                        <button type="submit" className="sr-search-btn" disabled={isSearching || !destinationQuery.trim()}>
                            {isSearching ? <span className="sr-spinner" /> : 'Go'}
                        </button>
                    </form>

                    {/* Autocomplete dropdown */}
                    {showSuggestions && suggestions.length > 0 && (
                        <div className="sr-autocomplete">
                            {suggestions.map(s => (
                                <div key={s.id} className="sr-autocomplete-item" onClick={() => selectSuggestion(s)}>
                                    <span className="sr-autocomplete-icon">📍</span>
                                    <div className="sr-autocomplete-text">
                                        <div className="sr-autocomplete-short">{s.short || s.display.split(',')[0]}</div>
                                        <div className="sr-autocomplete-full">{s.display}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Route mode toggle */}
                    <div className="sr-route-mode">
                        <button className={`sr-mode-btn ${routeMode === 'safest' ? 'active' : ''}`} onClick={() => setRouteMode('safest')} title="Safest">🛡️ Safest</button>
                        <button className={`sr-mode-btn ${routeMode === 'fastest' ? 'active' : ''}`} onClick={() => setRouteMode('fastest')} title="Balanced">⚡ Fastest Safe</button>
                    </div>

                    {searchError && <div className="sr-search-error">⚠️ {searchError}</div>}
                    {isCalculatingRoute && <div className="sr-calculating">🔄 Calculating safest route via real roads...</div>}
                </div>
            )}

            {/* ══ ROUTE INFO + START NAVIGATION (pre-nav) ══════════════════════════ */}
            {routeInfo && !isNavigating && (
                <div className="sr-route-card">
                    <div className="sr-route-stats">
                        <div className="sr-route-stat">
                            <span className="sr-route-icon">📍</span>
                            <span className="sr-route-val">{routeInfo.distance}</span>
                        </div>
                        <div className="sr-route-divider" />
                        <div className="sr-route-stat">
                            <span className="sr-route-icon">⏱️</span>
                            <span className="sr-route-val">{routeInfo.duration}</span>
                        </div>
                        <div className="sr-route-divider" />
                        <div className="sr-route-stat">
                            <span className="sr-route-icon">🛡️</span>
                            <span className={`sr-route-val ${routeInfo.safetyScore >= 80 ? 'safe' : routeInfo.safetyScore >= 60 ? 'moderate' : 'danger'}`}>
                                {routeInfo.safetyScore}%
                            </span>
                        </div>
                    </div>
                    <button className="sr-start-nav-btn" onClick={handleStartNavigation}>
                        <span>🧭</span> Start Navigation
                    </button>
                </div>
            )}

            {/* ══ LAYER CONTROLS ═══════════════════════════════════════════════════ */}
            {!isNavigating && (
                <div className="sr-layer-controls">
                    <button className={`sr-layer-btn ${showHeatmap ? 'on' : ''}`} onClick={() => setShowHeatmap(v => !v)} title="Toggle heatmap">🌡️</button>
                    <button className={`sr-layer-btn ${showHotspots ? 'on' : ''}`} onClick={() => setShowHotspots(v => !v)} title="Toggle markers">📍</button>
                    <button className={`sr-layer-btn ${showHazardZones ? 'on' : ''}`} onClick={() => setShowHazardZones(v => !v)} title="Toggle hazard zones">⚠️</button>
                </div>
            )}

            {/* ══ MAP ══════════════════════════════════════════════════════════════ */}
            <MapContainer
                center={mapCenter}
                zoom={userPos ? 13 : 6}
                className="sr-leaflet-map"
                whenCreated={handleMapReady}
                zoomControl={false}
            >
                <TileLayer
                    attribution='&copy; <a href="https://carto.com/" target="_blank">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OSM</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    subdomains="abcd"
                    maxZoom={19}
                />

                <MapFollower userPos={userPos} isNavigating={isNavigating} destination={destination} routeCoords={routeCoords} />

                {showHeatmap && <HeatmapLayer points={heatmapPoints} />}

                {/* Crime hotspot markers — hidden during active nav for clarity */}
                {showHotspots && !isNavigating && (
                    <LayerGroup>
                        {allHotspots.map(spot => (
                            <Marker key={spot.id} position={[spot.lat, spot.lng]} icon={createHotspotIcon(spot.risk)}
                                eventHandlers={{ click: () => { if (onMarkerClick) onMarkerClick(spot); } }}>
                                <Popup className="sr-popup">
                                    <div className="sr-popup-content">
                                        <div className="sr-popup-header" style={{ borderLeftColor: riskToColor(spot.risk) }}>
                                            <strong>{spot.name}</strong>
                                            <span className="sr-popup-province">{spot.province}</span>
                                        </div>
                                        <div className="sr-popup-badge" style={{ background: riskToColor(spot.risk) }}>{riskLabel(spot.risk)}</div>
                                        <div className="sr-popup-row"><b>Risk Level:</b> {Math.round(spot.risk * 100)}%</div>
                                        <div className="sr-popup-row"><b>Type:</b> {spot.type}</div>
                                        {spot.street && <div className="sr-popup-row"><b>Address:</b> {spot.street}</div>}
                                        <div className="sr-popup-row"><b>Note:</b> {spot.label}</div>
                                    </div>
                                </Popup>
                            </Marker>
                        ))}
                    </LayerGroup>
                )}

                {/* Hazard zones */}
                {showHazardZones && !isNavigating && (
                    <LayerGroup>
                        {allHotspots.filter(h => h.risk >= 0.75).map(h => (
                            <Circle key={`z_${h.id}`} center={[h.lat, h.lng]} radius={600}
                                pathOptions={{ fillColor: riskToColor(h.risk), fillOpacity: 0.12, color: riskToColor(h.risk), weight: 1.5, opacity: 0.5 }} />
                        ))}
                        {backendHazardZones.map((z, i) => (
                            <Circle key={`bz_${i}`} center={[z.center.lat, z.center.lng]} radius={z.radius || 500}
                                pathOptions={{ fillColor: z.fillColor || '#e41e26', fillOpacity: z.fillOpacity || 0.2, color: z.strokeColor || '#e41e26', weight: z.strokeWeight || 2, opacity: z.strokeOpacity || 0.8 }}
                                eventHandlers={{ click: () => { if (onHazardDetected) onHazardDetected(z); } }} />
                        ))}
                    </LayerGroup>
                )}

                {/* Route — white outline then color-coded */}
                {routeSegments.map((seg, i) => (
                    <Polyline key={`ro_${i}`} positions={seg.coords} pathOptions={{ color: '#fff', weight: isNavigating ? 14 : 12, opacity: 0.15 }} />
                ))}
                {routeSegments.map((seg, i) => (
                    <Polyline key={`rs_${i}`} positions={seg.coords} pathOptions={{ color: seg.color, weight: isNavigating ? 9 : 7, opacity: 0.93, lineCap: 'round', lineJoin: 'round' }} />
                ))}

                {/* User location */}
                {userPos && (
                    <Marker position={[userPos.lat, userPos.lng]} icon={createUserIcon(userHeading)} zIndexOffset={1000}>
                        <Popup><strong>📍 Your Location</strong></Popup>
                    </Marker>
                )}

                {/* Destination */}
                {destination && (
                    <Marker position={[destination.lat, destination.lng]} icon={createDestIcon()}>
                        <Popup className="sr-popup">
                            <div className="sr-popup-content">
                                <div className="sr-popup-badge" style={{ background: '#00cc66' }}>🏁 Destination</div>
                                <div className="sr-popup-row">{destinationQuery}</div>
                            </div>
                        </Popup>
                    </Marker>
                )}
            </MapContainer>

            {/* ══ NAVIGATION BOTTOM BAR ═════════════════════════════════════════════ */}
            {isNavigating && (
                <div className="sr-nav-bottom">
                    <div className="sr-nav-bottom-info">
                        <div className="sr-nav-bottom-stat">
                            <span className="sr-nav-bottom-label">Distance</span>
                            <span className="sr-nav-bottom-val">{distanceRemaining ? formatDist(parseFloat(distanceRemaining)) : '—'}</span>
                        </div>
                        <div className="sr-nav-bottom-divider" />
                        <div className="sr-nav-bottom-stat">
                            <span className="sr-nav-bottom-label">ETA</span>
                            <span className="sr-nav-bottom-val">{timeRemaining ? `${Math.round(timeRemaining)} min` : '—'}</span>
                        </div>
                        <div className="sr-nav-bottom-divider" />
                        <div className="sr-nav-bottom-stat">
                            <span className="sr-nav-bottom-label">Safety</span>
                            <span className={`sr-nav-bottom-val ${routeInfo?.safetyScore >= 80 ? 'safe' : routeInfo?.safetyScore >= 60 ? 'moderate' : 'danger'}`}>
                                {routeInfo?.safetyScore || '—'}%
                            </span>
                        </div>
                    </div>
                    <button className="sr-end-nav-btn" onClick={handleEndNavigation}>
                        ✕ End Navigation
                    </button>
                </div>
            )}

            {/* ══ LEGEND (hidden during navigation) ════════════════════════════════ */}
            {!isNavigating && (
                <div className="sr-legend">
                    <div className="sr-legend-title">🛡️ SafeRoute Legend</div>
                    <div className="sr-legend-item"><span className="sr-legend-dot" style={{ background: '#e41e26' }} />High Risk</div>
                    <div className="sr-legend-item"><span className="sr-legend-dot" style={{ background: '#ff7600' }} />Moderate Risk</div>
                    <div className="sr-legend-item"><span className="sr-legend-dot" style={{ background: '#ffc300' }} />Low-Moderate</div>
                    <div className="sr-legend-item"><span className="sr-legend-dot" style={{ background: '#00cc66' }} />Safe</div>
                    <div className="sr-legend-divider" />
                    <div className="sr-legend-item"><span className="sr-legend-line" style={{ background: '#00cc66' }} />Safe Road</div>
                    <div className="sr-legend-item"><span className="sr-legend-line" style={{ background: '#e41e26' }} />Danger Road</div>
                    <div className="sr-legend-footer">
                        <span className={`sr-live-dot ${backendConnected ? 'live' : 'offline'}`} />
                        {backendConnected ? `Live • ${allHotspots.length} hotspots` : `Offline • ${SA_CRIME_HOTSPOTS.length} hotspots`}
                    </div>
                </div>
            )}
        </div>
    );
};

export default SafeRouteMapComponent;
