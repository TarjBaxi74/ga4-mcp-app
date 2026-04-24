interface Props {
  rows: Record<string, string>[];
}

export default function DataTable({ rows }: Props) {
  if (!rows || rows.length === 0) return null;
  const cols = Object.keys(rows[0]);

  return (
    <div style={{ overflowX: "auto", marginTop: 12 }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c} style={{
                textAlign: "left", padding: "8px 12px",
                borderBottom: "1px solid #1f2937", color: "#6b7280",
              }}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c} style={{
                  padding: "8px 12px",
                  borderBottom: "1px solid #111827",
                  color: "#d1d5db",
                }}>{row[c]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}