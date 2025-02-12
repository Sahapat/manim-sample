from manimlib import *

class FourierCirclesScene(Scene):
    n_vectors = 10
    big_radius = 2
    colors = [
        BLUE_D,
        BLUE_C,
        BLUE_E,
        GREY_BROWN,
    ]
    circle_style = {
        "stroke_width": 2,
    }
    vector_config = {
        "buff": 0,
        "max_tip_length_to_length_ratio": 0.35,
        "fill_opacity": 0.75,
    }
    circle_config = {
        "stroke_width": 1,
        "stroke_opacity": 0.75,
    }
    base_frequency = 1
    slow_factor = 0.25
    center_point = ORIGIN
    parametric_function_step_size = 0.01
    drawn_path_color = YELLOW
    drawn_path_stroke_width = 2

    def setup(self):
        self.slow_factor_tracker = ValueTracker(self.slow_factor)
        self.vector_clock = ValueTracker(0)

        # Update function with single argument
        def update_vector_clock(m, dt):
            self.vector_clock.increment_value(self.get_slow_factor() * dt)

        self.vector_clock.add_updater(update_vector_clock)
        self.add(self.vector_clock)

    def get_slow_factor(self):
        return self.slow_factor_tracker.get_value()

    def get_vector_time(self):
        return self.vector_clock.get_value()

    def get_freqs(self):
        n = self.n_vectors
        all_freqs = list(range(n // 2, -n // 2, -1))
        all_freqs.sort(key=abs)
        return all_freqs
    
    def get_coefficients(self):
        return [complex(0) for x in range(self.n_vectors)]
    
    def get_color_iterator(self):
        return it.cycle(self.colors)
    
    def get_rotating_vectors(self, freqs=None, coefficients=None):
        vectors = VGroup()
        self.center_tracker = VectorizedPoint(self.center_point)
        if freqs is None:
            freqs = self.get_freqs()
        if coefficients is None:
            coefficients = self.get_coefficients()
        
        last_vector = None
        for freq, coefficient in zip(freqs, coefficients):
            if last_vector is not None:
                center_func = last_vector.get_end
            else:
                center_func = self.center_tracker.get_location
            vector = self.get_rotating_vector(
                coefficient=coefficient,
                freq=freq,
                center_func=center_func
            )
            vectors.add(vector)
            last_vector = vector
        return vectors

    def get_rotating_vector(self, coefficient, freq, center_func):
        vector = Vector(RIGHT, **self.vector_config)
        
        # Scale by magnitude of coefficient
        magnitude = abs(coefficient)
        phase = np.angle(coefficient) if magnitude != 0 else 0

        vector.stretch_to_fit_width(magnitude)  # Ensures proper scaling
        vector.rotate(phase)  # Rotate by computed phase
        vector.move_to(center_func())  # Ensure correct positioning
        
        # Store additional attributes
        vector.freq = freq
        vector.coefficient = coefficient
        vector.center_func = center_func

        # Attach updater
        vector.add_updater(self.update_vector)

        return vector

    def update_vector(self, vector, dt):
        time = self.get_vector_time()
        coef = vector.coefficient
        freq = vector.freq
        phase = np.angle(coef)  # Safer than np.log(coef).imag

        vector.set_length(abs(coef))
        vector.set_angle(phase + time * freq * TAU)
        vector.shift(vector.center_func() - vector.get_start())
        return vector

    def get_vector_time(self):
        return self.vector_clock.get_value()

    def get_circles(self, vectors):
        return VGroup(*[
            self.get_circle(vector, color)
            for vector, color in zip(vectors, self.get_color_iterator())
        ])

    def get_circle(self, vector, color=BLUE):
        circle = Circle(color=color, **self.circle_config)
        circle.center_func = vector.get_start
        circle.radius_func = vector.get_length
        circle.add_updater(self.update_circle)
        return circle

    def update_circle(self, circle):
        circle.set_height(2 * circle.radius_func())  # Ensure correct scaling
        circle.move_to(circle.center_func())  # Move circle to vector start
        return circle

    def get_vector_sum_path(self, vectors, color=YELLOW):
        coefs = [v.coefficient for v in vectors]
        freqs = [v.freq for v in vectors]
        center = vectors[0].get_start()

        path = ParametricCurve(
            lambda t: center + reduce(op.add, [
                complex_to_R3(coef * np.exp(TAU * 1j * freq * t))
                for coef, freq in zip(coefs, freqs)
            ]),
            t_range=[0, 1, self.parametric_function_step_size],
            color=color,
            stroke_width=self.drawn_path_stroke_width,  # Ensure correct stroke width
        )
        return path

    def get_drawn_path_alpha(self):
        return self.get_vector_time()

    def get_drawn_path(self, vectors, stroke_width=None, fade_rate=0.2, **kwargs):
        if stroke_width is None:
            stroke_width = self.drawn_path_stroke_width
        path = self.get_vector_sum_path(vectors, **kwargs)
        path.set_stroke(self.drawn_path_color, stroke_width)
        self.add_path_fader(path, fade_rate)
        return path

    def add_path_fader(self, path, fade_rate=0.2):
        stroke_width = np.max(path.get_stroke_width())
        stroke_opacity = np.max(path.get_stroke_opacity())

        def update_path(m, dt):
            alpha = self.get_vector_time()
            n = path.get_num_points()
            if n == 0:
                return path
            fade_factors = (np.linspace(0, 1, n) - alpha) % 1
            fade_factors = fade_factors**fade_rate
            path.set_stroke(
                width=stroke_width * fade_factors,
                opacity=stroke_opacity * fade_factors,
            )

        path.add_updater(update_path)
        return path

    def get_y_component_wave(self, vectors, left_x=1, color=PINK, n_copies=2, right_shift_rate=5):
        path = self.get_vector_sum_path(vectors)
        wave = ParametricCurve(
            lambda t: op.add(
                right_shift_rate * t * LEFT,
                path.underlying_function(t)[1] * UP
            ),
            t_range=[0, 1],
            color=color,
        )

        wave_copies = VGroup(*[wave.copy() for _ in range(n_copies)])
        wave_copies.arrange(RIGHT, buff=0)
        top_point = wave_copies.get_top()

        wave.creation = ShowCreation(
            wave,
            run_time=(1 / self.get_slow_factor()),
            rate_func=linear,
        )
        self.play(wave.creation)  # Replaces cycle_animation(wave.creation)

        wave.add_updater(lambda m: m.shift((m.get_left()[0] - left_x) * LEFT))

        def update_wave_copies(wcs):
            index = int(wave.creation.total_time * self.get_slow_factor())
            wcs[:index].match_style(wave)
            wcs[index:].set_stroke(width=0)
            wcs.next_to(wave, RIGHT, buff=0)
            wcs.align_to(top_point, UP)

        wave_copies.add_updater(update_wave_copies)
        return VGroup(wave, wave_copies)

    def get_wave_y_line(self, vectors, wave):
        return DashedLine(
            vectors[-1].get_end(),
            wave[0].get_end(),
            stroke_width=1,
            dash_length=DEFAULT_DASH_LENGTH * 0.5,
        )

    def get_coefficients_of_path(self, path, n_samples=10000, freqs=None):
        if freqs is None:
            freqs = self.get_freqs()
        dt = 1 / n_samples
        ts = np.linspace(0, 1, n_samples)
        samples = np.array([path.point_from_proportion(t) for t in ts])
        samples -= self.center_point
        complex_samples = samples[:, 0] + 1j * samples[:, 1]

        result = [
            (np.exp(-TAU * 1j * freq * ts) * complex_samples).sum() * dt
            for freq in freqs
        ]

        return result

class FourierOfPiSymbol(FourierCirclesScene):
    n_vectors=101
    center_point=ORIGIN
    slow_factor=0.1
    n_cycles=1
    tex="\\pi"
    start_drawn=False
    max_circle_stroke_width=1

    def construct(self):
        self.add_vectors_circles_path()
        for _ in range(self.n_cycles):
            self.run_one_cycle()

    def add_vectors_circles_path(self):
        path = self.get_path()
        coefs = self.get_coefficients_of_path(path)

        for freq, coef in zip(self.get_freqs(), coefs):
            print(freq, "\t", coef)

        vectors = self.get_rotating_vectors(coefficients=coefs)
        circles = self.get_circles(vectors)
        self.set_decreasing_stroke_widths(circles)

        drawn_path = self.get_drawn_path(vectors)
        if self.start_drawn:
            self.vector_clock.increment_value(1)

        self.add(path, vectors, circles, drawn_path)

        # Store references
        self.vectors = vectors
        self.circles = circles
        self.path = path
        self.drawn_path = drawn_path

    def run_one_cycle(self):
        self.wait(1 / self.slow_factor)

    def set_decreasing_stroke_widths(self, circles):
        mcsw = self.max_circle_stroke_width
        for k, circle in zip(it.count(1), circles):
            circle.set_stroke(width=max(mcsw / k, mcsw))
        return circles

    def get_path(self):
        tex_mob = Tex(self.tex)  # OldTex is replaced with MathTex
        tex_mob.set_height(6)
        path = tex_mob.family_members_with_points()[0]
        path.set_fill(opacity=0)
        path.set_stroke(WHITE, 1)
        return path
