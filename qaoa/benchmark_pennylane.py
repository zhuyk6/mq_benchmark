import pennylane as qml
from pennylane import qaoa
from pennylane import numpy as np
import random


def bench(hyperparams={}):
    """
    Performs QAOA optimizations.

    Args:
        hyperparams (dict): hyperparameters to configure this benchmark

                * 'graph': Graph represented as a NetworkX Graph class

                * 'n_layers': Number of layers in the QAOA circuit

                * 'params': Numpy array of trainable parameters that is fed into the circuit

                * 'shots': The number of samples.
    """

    graph = hyperparams['graph']
    n_layers = hyperparams['n_layers']
    shots = hyperparams['shots']

    n_wires = len(graph.nodes)
    wires = range(n_wires)

    device = qml.device("default.qubit", wires=n_wires, shots=shots)

    cost_h, mixer_h = qaoa.maxcut(graph)
    # print("Cost Hamiltonian", cost_h)
    # print("Mixer Hamiltonian", mixer_h)

    def qaoa_layer(gamma, alpha):
        qaoa.cost_layer(gamma, cost_h)
        qaoa.mixer_layer(alpha, mixer_h)

    def circuit(params):
        for i in wires:
            qml.Hadamard(wires=i)
        qml.layer(qaoa_layer, n_layers, params[0], params[1])

    @qml.qnode(device)
    def cost_function(params):
        circuit(params)
        return qml.expval(cost_h)

    @qml.qnode(device)
    def probability_circuit(gamma, alpha):
        circuit([gamma, alpha])
        return qml.probs(wires=wires)

    if 'params' in hyperparams:
        params = hyperparams['params']
    else:
        single_param_for_all_layers = [random.random() for i in range(n_layers)]
        params = np.array([single_param_for_all_layers, single_param_for_all_layers], requires_grad=True)  # 将每个初始参数设置为 0.5
        optimizer = qml.GradientDescentOptimizer()
        steps = 100
        for i in range(steps):
            params = optimizer.step(cost_function, params)

        # print("Optimal Parameters: \n", params)

    probs_measured = probability_circuit(params[0], params[1])
    print("Probability distribution of measurement result with PennyLane: \n", probs_measured)
