/**
 * Mock adapter: outputs the Alliance input schema without calling any provider.
 * Used to validate the ingestion flow and API. Replace with real adapters
 * that fetch from provider APIs and map responses to our 3-axis schema.
 *
 * Schema (v2.0 methodology):
 *   Each layer (asset, market, vault) has exactly 3 axes: security, operations, economics.
 *   Each axis is a numeric 0–10 (higher = safer) or null (unknown).
 *
 * To be counted in a layer, an adapter must supply all 3 axes (value or null).
 * Null is filled with the mean of other adapters' values for that axis.
 */

const PROVIDER = 'mock';

const ASSET_AXES = ['security', 'operations', 'economics'];
const MARKET_AXES = ['security', 'operations', 'economics'];
const VAULT_AXES = ['security', 'operations', 'economics'];

function getAssetInputs(entityId, timestamp = new Date().toISOString()) {
  return {
    entity_type: 'asset',
    entity_id: entityId,
    provider: PROVIDER,
    timestamp,
    dimensions: {
      security: 8,    // Lindy, bug bounty, audits
      operations: 7,  // Documentation, reserves, compliance
      economics: 9,   // Depeg risk, collateral quality, liquidity
    },
  };
}

function getMarketInputs(entityId, timestamp = new Date().toISOString()) {
  return {
    entity_type: 'market',
    entity_id: entityId,
    provider: PROVIDER,
    timestamp,
    dimensions: {
      security: 7,    // Protocol Lindy, bug bounty, audits
      operations: 8,  // Governance/timelock, oracle quality, parameters
      economics: 6,   // Strategy risk, volatility, liquidation risk
    },
  };
}

function getVaultInputs(entityId, timestamp = new Date().toISOString()) {
  return {
    entity_type: 'vault',
    entity_id: entityId,
    provider: PROVIDER,
    timestamp,
    dimensions: {
      security: 7,    // Vault Lindy, bug bounty, audits
      operations: 6,  // Governance controls, withdrawal liquidity, pause
      economics: 8,   // Strategy quality / underlying market quality
    },
  };
}

/** Example with null axes — adapter is still counted; nulls filled by other providers' mean. */
function getVaultInputsWithNulls(entityId, timestamp = new Date().toISOString()) {
  return {
    entity_type: 'vault',
    entity_id: entityId,
    provider: PROVIDER,
    timestamp,
    dimensions: {
      security: 7,
      operations: null,
      economics: null,
    },
  };
}

async function fetchAssetInputs(chainId, tokenAddress) {
  const entityId = `${chainId}:${tokenAddress}`;
  return [getAssetInputs(entityId)];
}

async function fetchMarketInputs(chainId, protocolSlug, marketId) {
  const entityId = `${chainId}:${protocolSlug}:${marketId}`;
  return [getMarketInputs(entityId)];
}

async function fetchVaultInputs(chainId, vaultAddress) {
  const entityId = `${chainId}:${vaultAddress}`;
  return [getVaultInputs(entityId)];
}

module.exports = {
  fetchAssetInputs,
  fetchMarketInputs,
  fetchVaultInputs,
  getAssetInputs,
  getMarketInputs,
  getVaultInputs,
  getVaultInputsWithNulls,
  ASSET_AXES,
  MARKET_AXES,
  VAULT_AXES,
  PROVIDER,
};
