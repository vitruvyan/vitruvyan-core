// utils/textSafety.js
export const ensureString = (input, fallback = "") => {
  // Se è già una stringa, restituiscila
  if (typeof input === "string") {
    return input
  }

  // Se è null o undefined, usa il fallback
  if (input === null || input === undefined) {
    return fallback
  }

  // Se è un oggetto o array, convertilo in JSON leggibile
  if (typeof input === "object") {
    try {
      return JSON.stringify(input, null, 2)
    } catch (e) {
      return String(input)
    }
  }

  // Per tutti gli altri tipi, converti in stringa
  return String(input)
}

// Funzione helper per debug
export const debugInput = (input, functionName) => {
  if (process.env.NODE_ENV === "development") {
    console.log(`[${functionName}] Input debug:`, {
      type: typeof input,
      value: input,
      isString: typeof input === "string",
      length: input?.length || "N/A",
    })
  }
}
