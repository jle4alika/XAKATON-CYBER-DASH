import { postSimulationControl } from './api'

export const pauseSimulation = () => postSimulationControl({ action: 'pause' })
export const resumeSimulation = (speed = 1) =>
  postSimulationControl({
    action: 'resume',
    speed,
  })
export const setSimulationSpeed = (speed) => postSimulationControl({ speed })

