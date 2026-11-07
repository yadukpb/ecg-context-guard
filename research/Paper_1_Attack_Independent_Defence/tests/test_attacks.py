import torch

from Paper_1_Attack_Independent_Defence.adversarial_attacks import attacks


class _TinyLinearModel(torch.nn.Module):
    """A trivial 2-class model so attack-shape/behaviour can be tested without a full
    ResNet-18 training run."""

    def __init__(self):
        super().__init__()
        self.fc = torch.nn.Linear(4, 2)

    def forward(self, x):
        return self.fc(x.flatten(1))


def test_fgsm_perturbation_is_bounded_by_epsilon():
    model = _TinyLinearModel()
    x = torch.randn(3, 1, 4)
    y = torch.tensor([0, 1, 0])
    epsilon = 0.05
    x_adv = attacks.fgsm_attack(model, x, y, epsilon)
    assert torch.all((x_adv - x).abs() <= epsilon + 1e-6)
    assert x_adv.shape == x.shape


def test_pgd_perturbation_stays_within_epsilon_ball():
    model = _TinyLinearModel()
    x = torch.randn(2, 1, 4)
    y = torch.tensor([1, 0])
    epsilon = 0.1
    x_adv = attacks.pgd_attack(model, x, y, epsilon, iterations=5)
    assert torch.all((x_adv - x).abs() <= epsilon + 1e-5)


def test_simplified_boundary_walk_returns_same_shape():
    model = _TinyLinearModel()
    x = torch.randn(1, 1, 4)
    with torch.no_grad():
        orig_class = int(model(x).argmax(dim=1).item())
    x_adv = attacks.simplified_boundary_walk(model, x, orig_class, epsilon=0.2, max_queries=30)
    assert x_adv.shape == x.shape
