from manimlib import *
from scipy.integrate import odeint
from scipy.integrate import solve_ivp

def lorenz_system(t, state, sigma=10, rho=28, beta=8 / 3):
    x, y, z = state
    dxdt = sigma * (y - x)
    dydt = x * (rho - z) - y
    dzdt = x * y - beta * z
    return [dxdt, dydt, dzdt]


def ode_solution_points(function, state0, time, dt=0.01):
    solution = solve_ivp(
        function,
        t_span=(0, time),
        y0=state0,
        t_eval=np.arange(0, time, dt)
    )
    return solution.y.T


class LorenzAttractor(InteractiveScene):
    def construct(self):
        lorenz_description = Text(
            "The Lorenz system is given by the following set of ordinary differential equations:",
            font_size=18
        )
        lorenz_description.to_corner(UL)
        lorenz_description.fix_in_frame()
        lorenz_description.set_backstroke()
        self.play(Write(lorenz_description))

        # # Add the equations
        lorenz_equations = Tex(
            R"""
                \begin{aligned}
                \frac{\mathrm{d} x}{\mathrm{~d} t} & =\sigma(y-x) \\
                \frac{\mathrm{d} y}{\mathrm{~d} t} & =x(\rho-z)-y \\
                \frac{\mathrm{d} z}{\mathrm{~d} t} & =x y-\beta z
                \end{aligned}
            """,
            t2c={
                "x": RED,
                "y": GREEN,
                "z": BLUE,
            },
            font_size=30
        )
        lorenz_equations.fix_in_frame()
        lorenz_equations.to_corner(UL)
        lorenz_equations.set_backstroke()
        lorenz_equations.shift(DOWN * 0.5)
        self.play(Write(lorenz_equations))

        # Set up axes
        axes = ThreeDAxes(
            x_range=(-50, 50, 5),
            y_range=(-50, 50, 5),
            z_range=(-0, 50, 5),
            width=16,
            height=16,
            depth=8,
        )
        axes.set_width(FRAME_WIDTH)
        axes.center()

        self.frame.reorient(43, 76, 1, IN, 10)
        self.frame.add_updater(lambda m, dt: m.increment_theta(dt * 3 * DEGREES))
        self.play(ShowCreation(axes, run_time=2))

        # Compute a set of solutions
        epsilon = 1e-5
        evolution_time = 15
        n_points = 5
        states = [
            [10, 10, 10 + n * epsilon]
            for n in range(n_points)
        ]
        colors = color_gradient([BLUE_E, RED_E], len(states))

        curves = VGroup()
        for state, color in zip(states, colors):
            points = ode_solution_points(lorenz_system, state, evolution_time)
            curve = VMobject().set_points_smoothly(axes.c2p(*points.T))
            curve.set_stroke(color, 1, opacity=0.25)
            curves.add(curve)

        curves.set_stroke(width=2, opacity=1)
        python_code = Code(
            R'''
            ode_solution = solve_ivp(
                lambda: lambda state, sigma=10, rho=28, beta=8/3: [
                    sigma * (state[1] - state[0]),  # dx/dt
                    state[0] * (rho - state[2]) - state[1],  # dy/dt
                    state[0] * state[1] - beta * state[2]  # dz/dt
                ],
                t_span=(0, 15),
                y0=[
                    [10, 10, 10 + n * epsilon]
                    for n in range(5)
                ],
                t_eval=np.arange(0, 15, 0.01)
            )
            ''',
            font_size=18
        )
        python_code.fix_in_frame()
        python_code.to_corner(DR)
        python_code.set_backstroke()
        self.play(*(
            ShowCreation(curve)
            for curve in curves
        ),
        ShowCreation(python_code),
        run_time=evolution_time)

        self.wait(5)

        # # Display dots moving along those trajectories
        # dots = Group(GlowDot(color=color, radius=0.25) for color in colors)

        # def update_dots(dots, curves=curves):
        #     for dot, curve in zip(dots, curves):
        #         dot.move_to(curve.get_end())

        # dots.add_updater(update_dots)

        # tail = VGroup(
        #     TracingTail(dot, time_traced=3).match_color(dot)
        #     for dot in dots
        # )

        # self.add(dots)
        # self.add(tail)
        # curves.set_opacity(0)
        # self.play(
        #     *(
        #         ShowCreation(curve, rate_func=linear)
        #         for curve in curves
        #     ),
        #     run_time=evolution_time,
        # )
