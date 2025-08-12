'use client';

import { useEffect, useState } from 'react';

export default function EmployeeSection() {
  const [employees, setEmployees] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('http://localhost:8000/api/employees', {
      credentials: 'include', // send cookies for session
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch employees');
        return res.json();
      })
      .then(data => setEmployees(data))
      .catch(err => setError(err.message));
  }, []);

  if (error) return <p>Error: {error}</p>;

  return (
    <div>
      <h1>Employees</h1>
      <ul>
        {employees.map((emp) => (
          <li key={emp[0]}>
            {emp[1]} {emp[2]} — {emp[4]} ({emp[5]})
          </li>
        ))}
      </ul>
    </div>
  );
}
