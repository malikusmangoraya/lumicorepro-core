export const doctor = {
  name: 'Dr. Ayesha Siddiqui',
  role: 'Consultant Cardiologist',
  id: 'Room 12 · Cardiology',
};

export const chat = [
  { from: 'doctor', text: "Ayaan, good morning. I'm reviewing your latest ECG and lipid panel." },
  {
    from: 'patient',
    text: "Assalam-o-Alaikum Doctor. I've been taking the new dose since Monday.",
  },
  { from: 'doctor', text: 'Great. Your LDL dropped from 168 to 141 — keep it up. Any dizziness?' },
  { from: 'patient', text: 'None at all. Feeling much more energetic actually.' },
];

export const controls = [
  { label: 'Microphone' },
  { label: 'Camera' },
  { label: 'Screen Share' },
  { label: 'Chat' },
  { label: 'End Call' },
];
