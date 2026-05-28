/**
 * Minimal API server: returns mock vault data so the structure is runnable.
 * Replace with real DB reads once ingestion is wired.
 * Run: node server.js  (or npm start). Listens on PORT or 3000.
 */

const http = require('http');

const PORT = process.env.PORT || 3000;

function send(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(body));
}

const mockVault = {
  entity_id: '1:0x0000000000000000000000000000000000000001',
  score: 8.1,
  layers: {
    asset:  { score: 8.0, security: 8, operations: 7, economics: 9 },
    market: { score: 7.0, security: 7, operations: 8, economics: 6 },
    vault:  { score: 6.8, security: 7, operations: 6, economics: 8 },
  },
  methodology_version: 'v2.1',
  updated_at: new Date().toISOString(),
  inputs_by_provider: {
    mock: {
      asset:  { security: 8, operations: 7, economics: 9 },
      market: { security: 7, operations: 8, economics: 6 },
      vault:  { security: 7, operations: 6, economics: 8 },
    },
  },
};

const server = http.createServer((req, res) => {
  const url = new URL(req.url || '', `http://localhost:${PORT}`);
  const path = url.pathname;
  const id = path.match(/^\/vaults\/([^/]+)$/)?.[1];

  if (req.method === 'GET' && path === '/vaults') {
    return send(res, 200, [mockVault]);
  }
  if (req.method === 'GET' && id) {
    if (path === `/vaults/${id}`) return send(res, 200, { ...mockVault, entity_id: id });
    if (path === `/vaults/${id}/history`) return send(res, 200, [{ timestamp: mockVault.updated_at, score: mockVault.score, layers: mockVault.layers }]);
    if (path === `/vaults/${id}/providers`) return send(res, 200, { entity_id: id, providers: { mock: { dimensions: mockVault.inputs_by_provider.mock, timestamp: mockVault.updated_at } } });
  }

  send(res, 404, { error: 'Not found' });
});

server.listen(PORT, () => console.log(`API listening on http://localhost:${PORT}`));
