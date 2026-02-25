/**
 * VEE ADAPTER - Bridge between VitruvyanResponse and VEEAccordions
 *
 * Maps evidence.vee or vee_explanations from VitruvyanResponse
 * to the props expected by VEEAccordions component.
 *
 * @param {Object} vitruvyanResponse - The unified response object
 * @returns {Object} - Props for VEEAccordions component
 */

export function adaptVEEForAccordion(vitruvyanResponse) {
  if (!vitruvyanResponse) return null

  // Extract VEE data from evidence or direct vee_explanations
  const veeData = vitruvyanResponse.evidence?.vee || vitruvyanResponse.vee_explanations

  if (!veeData || Object.keys(veeData).length === 0) {
    return null
  }

  // Map to VEEAccordions props
  return {
    veeExplanations: veeData,
    explainability: vitruvyanResponse.explainability,
    numericalPanel: vitruvyanResponse.numerical_panel
  }
}