/**
 * index.ts — Point d'entrée unique de la couche API : `import { api } from "@/api"`.
 */

export * as dossiers from "./dossiers";
export * as analyse from "./analyse";
export * as jurisprudence from "./jurisprudence";
export * as notes from "./notes";
export * as greffier from "./greffier";
export * as chat from "./chat";
export * as intention from "./intention";
export * as config from "./config";

export { ApiError, downloadBlob } from "./http";
export { obtenirClePersonnelle, definirClePersonnelle } from "./cleApiPersonnelle";
export type * from "./types";
export type { ConfigServeur } from "./config";
